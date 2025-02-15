import os
import re
import bibtexparser

# Define the file paths
BIBTEX_FILE = "main.bib"  # Ensure this matches your actual filename
OUTPUT_DIR = "markdown_entries"

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load the BibTeX file
with open(BIBTEX_FILE, "r", encoding="utf-8") as bibfile:
    bib_database = bibtexparser.load(bibfile)

# Function to format ordinal numbers (1st, 2nd, 3rd, etc.)
def ordinal(n):
    return f"{n}{'st' if n == 1 else 'nd' if n == 2 else 'rd' if n == 3 else 'th'}"

# Function to format BibTeX entry types as readable tags
def format_reference_type(entry_type):
    ref_map = {
        "book": "Book",
        "article": "Journal",
        "incollection": "Book_Chapter",
    }
    return ref_map.get(entry_type.lower(), entry_type.title())

# Function to process keywords into tags
def process_keywords(keyword_str):
    if not keyword_str:
        return []
    
    # Remove special characters, split keywords, and clean them up
    keywords = keyword_str.replace("\\", "").split(";")  # Remove `\` and split by `;`
    cleaned_keywords = []
    
    for kw in keywords:
        kw = kw.strip().lstrip("_")  # Trim spaces and remove leading underscores
        kw = re.sub(r"\(.*?\)", "", kw)  # Remove text in parentheses
        kw = re.sub(r"[+]", "", kw)  # Remove plus signs (`+`)
        kw = re.sub(r"(\.\d+)", "", kw)  # Remove decimal numbers (e.g., "4.0" → "4")
        kw = kw.replace(" ", "-")  # Replace spaces with hyphens
        if kw:  # Only add non-empty keywords
            cleaned_keywords.append(kw)
    
    return cleaned_keywords

# Function to format bibliography in Chicago 17th Edition
def format_chicago_bibliography(authors, year, title, journal, volume, issue, pages, publisher, url, doi):
    formatted_authors = ", ".join(authors)
    
    # Construct citation based on entry type
    if journal:  # Journal articles
        bibliography = f"{formatted_authors}. {year}. “{title}.” *{journal}* {volume} ({issue}): {pages}. {f'https://doi.org/{doi}' if doi else url}"
    elif publisher:  # Books
        bibliography = f"{formatted_authors}. {year}. *{title}*. {publisher}. {f'https://doi.org/{doi}' if doi else url}"
    else:  # Default
        bibliography = f"{formatted_authors}. {year}. *{title}*. {f'https://doi.org/{doi}' if doi else url}"
    
    return bibliography.rstrip(".")  # Remove trailing period to avoid breaking links

for entry in bib_database.entries:
    key = entry.get("ID", "unknown_key")
    
    # Get title, replace colons with hyphens, and remove line breaks
    title = entry.get("title", "Untitled").replace(":", " - ")
    title = " ".join(title.splitlines())

    year = entry.get("year", "Unknown Year")

    # Get reference type as tag
    ref_type = format_reference_type(entry.get("ENTRYTYPE", "Unknown"))

    # Get authors in "First Last" format
    raw_authors = entry.get("editor", entry.get("author", "Unknown Author"))
    authors_list = raw_authors.split(" and ") if raw_authors else []
    formatted_authors = [
        f"{name.split(', ')[1]} {name.split(', ')[0]}" if ", " in name else name for name in authors_list
    ]

    # Get metadata fields if available
    journal = entry.get("journal", "").replace(":", " - ")  # Replace colons in journal names
    journal = " ".join(journal.splitlines())  # Prevent unintended line breaks

    volume = entry.get("volume", "")
    issue = entry.get("number", "")
    pages = entry.get("pages", "")
    publisher = entry.get("publisher", "")
    affiliation = entry.get("affiliation", "")

    url = entry.get("url", "").strip()
    doi = entry.get("doi", "").strip()

    # Process keywords into tags
    keyword_tags = process_keywords(entry.get("keywords", ""))

    # Format bibliography in Chicago 17th Edition
    bibliography = format_chicago_bibliography(formatted_authors, year, title, journal, volume, issue, pages, publisher, url, doi)

    # Get abstract if available
    abstract = entry.get("abstract", "").strip()
    abstract = " ".join(abstract.split())  # Removes unwanted line breaks
    abstract_section = f"\n## Abstract\n{abstract}" if abstract else ""

    # Markdown content format
    markdown_content = f"""---
title: {title}
year: {year}
{"\n".join([f'author - {ordinal(i+1)}: "[[{author}]]"' for i, author in enumerate(formatted_authors)])}
key: "[[{key}]]"
{"journal: " + journal if journal else ""}
{"publisher: " + publisher if publisher else ""}
{"affiliation: " + affiliation if affiliation else ""}
tags:
  - {ref_type}
  {"\n  - ".join(keyword_tags) if keyword_tags else ""}
---

## Bibliography
{bibliography}
{abstract_section}
"""

    # Save as a Markdown file
    md_filename = os.path.join(OUTPUT_DIR, f"{key}.md")
    with open(md_filename, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content.strip())  # Strip excess newlines

print(f"Markdown files created in {OUTPUT_DIR}/")
