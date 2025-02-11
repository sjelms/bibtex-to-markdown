import os
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

# Function to map BibTeX entry types to formatted tags
def format_reference_type(entry_type):
    if entry_type.lower() == "book":
        return "Book"
    elif entry_type.lower() == "incollection":
        return "Book_Chapter"
    else:
        return entry_type.title()  # Convert other types to Title Case

for entry in bib_database.entries:
    key = entry.get("ID", "unknown_key")
    
    # Get title, replace colons with hyphens, and remove line breaks
    title = entry.get("title", "Untitled").replace(":", " - ")
    title = " ".join(title.splitlines())

    year = entry.get("year", "Unknown Year")

    # Get reference type and format as tag
    ref_type = format_reference_type(entry.get("ENTRYTYPE", "Unknown"))

    # Get authors, ensuring "First Last" format and no line breaks
    raw_authors = entry.get("editor", entry.get("author", "Unknown Author"))
    authors_list = raw_authors.split(" and ") if raw_authors else []
    
    formatted_authors = "\n".join(
        [f'author - {ordinal(i+1)}: "[[{name.split(", ")[1]} {name.split(", ")[0]}]]"'
         if ", " in name else f'author - {ordinal(i+1)}: "[[{name}]]"'
         for i, name in enumerate(authors_list)]
    )

    url = entry.get("url", "")
    doi = entry.get("doi", "")
    publisher = entry.get("publisher", "Unknown Publisher")

    # Get abstract if available, remove extra spaces, and force single-line formatting
    abstract = entry.get("abstract", "").strip()
    abstract = " ".join(abstract.split())  # This removes unwanted line breaks

    # Add the abstract section only if an abstract exists
    abstract_section = f"\n## Abstract\n{abstract}" if abstract else ""

    # Markdown content format
    markdown_content = f"""---
title: {title}
year: {year}
{formatted_authors}
key: "[[{key}]]"
tags:
  - {ref_type}
---

## Bibliography
{", ".join(authors_list)}. ({year}). _{title}_. {publisher}. {"https://doi.org/" + doi if doi else url}

{abstract_section}
"""

    # Save as a Markdown file
    md_filename = os.path.join(OUTPUT_DIR, f"{key}.md")
    with open(md_filename, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content)

print(f"Markdown files created in {OUTPUT_DIR}/")
