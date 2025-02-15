import os
import re
import bibtexparser

# Define file paths
BIBTEX_FILE = "main.bib"
OUTPUT_DIR = "markdown_entries"

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load the BibTeX file
with open(BIBTEX_FILE, "r", encoding="utf-8") as bibfile:
    bib_database = bibtexparser.load(bibfile)

# Function to format BibTeX entry types as readable tags
def format_reference_type(entry_type):
    ref_map = {"book": "Book", "article": "Journal", "incollection": "Book_Chapter"}
    return ref_map.get(entry_type.lower(), entry_type.title())

# Function to process keywords into tags (correcting spacing & colons)
def process_keywords(keyword_str):
    if not keyword_str:
        return []
    keywords = keyword_str.replace("\\", "").split(";")
    cleaned_keywords = []
    for kw in keywords:
        kw = kw.strip().lstrip("_")
        kw = re.sub(r"\(.*?\)", "", kw)  # Remove text in parentheses
        kw = re.sub(r"[+]", "", kw)  # Remove plus signs (`+`)
        kw = re.sub(r"(\.\d+)", "", kw)  # Remove decimal numbers (e.g., "4.0" → "4")
        kw = re.sub(r"\s+", "-", kw)  # Replace all spaces with hyphens
        kw = kw.replace(":", "-")  # **Fix: Remove colons and replace with hyphens**
        kw = kw.rstrip("-")  # Remove trailing hyphens
        if kw:
            cleaned_keywords.append(kw)
    return cleaned_keywords

# Function to format bibliography in Chicago 17th Edition
def format_chicago_bibliography(authors, year, title, journal, volume, issue, pages, publisher, url, doi):
    formatted_authors = ", ".join(authors)
    if journal:
        bibliography = f'{formatted_authors}. {year}. “{title}.” *{journal}* {volume} ({issue}): {pages}. {f"https://doi.org/{doi}" if doi else url}'
    elif publisher:
        bibliography = f'{formatted_authors}. {year}. *{title}*. {publisher}. {f"https://doi.org/{doi}" if doi else url}'
    else:
        bibliography = f'{formatted_authors}. {year}. *{title}*. {f"https://doi.org/{doi}" if doi else url}'
    return bibliography.rstrip(".")

for entry in bib_database.entries:
    key = entry.get("ID", "unknown_key")
    title = entry.get("title", "Untitled").replace(":", " - ")
    title = " ".join(title.splitlines())
    year = entry.get("year", "Unknown Year")
    ref_type = format_reference_type(entry.get("ENTRYTYPE", "Unknown"))

    # **Get authors in "First Last" format**
    raw_authors = entry.get("editor", entry.get("author", "Unknown Author"))
    authors_list = raw_authors.split(" and ") if raw_authors else []
    formatted_authors = [
        f"{name.split(', ')[1]} {name.split(', ')[0]}" if ", " in name else name
        for name in authors_list
    ]

    # Get metadata fields if available
    journal = entry.get("journal", "").replace(":", " - ")
    journal = " ".join(journal.splitlines())

    volume = entry.get("volume", "")
    issue = entry.get("number", "")
    pages = entry.get("pages", "")
    publisher = entry.get("publisher", "")
    affiliation = entry.get("affiliation", "")

    url = entry.get("url", "").strip()
    doi = entry.get("doi", "").strip()

    # Process keywords into tags
    keyword_tags = process_keywords(entry.get("keywords", ""))

    # Format bibliography
    bibliography = format_chicago_bibliography(formatted_authors, year, title, journal, volume, issue, pages, publisher, url, doi)

    # Get abstract if available
    abstract = entry.get("abstract", "").strip()
    abstract = " ".join(abstract.split())
    abstract_section = f"\n## Abstract\n{abstract}" if abstract else ""

    # **Ensure correct YAML formatting (handling any number of authors)**
    yaml_lines = [
        "---",
        f"title: {title}",
        f"year: {year}",
    ]
    
    for i, author in enumerate(formatted_authors, start=1):
        yaml_lines.append(f'author - {i}: "[[{author}]]"')

    yaml_lines.append(f'key: "[[{key}]]"')

    if journal:
        yaml_lines.append(f"journal: {journal}")
    if publisher:
        yaml_lines.append(f"publisher: {publisher}")
    if affiliation:
        yaml_lines.append(f"affiliation: {affiliation}")

    yaml_lines.append("tags:")

    # **Fix: Ensure no blank lines and all tags are single-line entries**
    tag_lines = [f"  - {ref_type}"] + [f"  - {tag}" for tag in keyword_tags]
    yaml_lines.extend(tag_lines)  # Ensures tags list is continuous

    yaml_lines.append("---")

    # Combine everything for Markdown output
    markdown_content = "\n".join(yaml_lines) + f"\n\n## Bibliography\n{bibliography}{abstract_section}"

    # Save as a Markdown file
    md_filename = os.path.join(OUTPUT_DIR, f"{key}.md")
    with open(md_filename, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content.strip())

print(f"Markdown files created in {OUTPUT_DIR}/")
