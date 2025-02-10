import os
import bibtexparser

# Load and parse the BibTeX file
BIBTEX_FILE = "references.bib"  # Update if your file has a different name
OUTPUT_DIR = "markdown_entries"  # Directory where Markdown files will be saved

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Read the BibTeX file
with open(BIBTEX_FILE, "r", encoding="utf-8") as bibfile:
    bib_database = bibtexparser.load(bibfile)

for entry in bib_database.entries:
    key = entry.get("ID", "unknown_key")
    title = entry.get("title", "Untitled")
    year = entry.get("year", "Unknown Year")
    authors = entry.get("editor", entry.get("author", "Unknown Author"))
    url = entry.get("url", "")
    doi = entry.get("doi", "")
    publisher = entry.get("publisher", "Unknown Publisher")

    # Convert authors to Markdown link format
    authors_list = authors.split(" and ") if authors else []
    formatted_authors = "\n".join(
        [f'author - {i+1}: "[[{author}]]"' for i, author in enumerate(authors_list)]
    )

    # Markdown content format
    markdown_content = f"""---
title: {title}
year: {year}
{formatted_authors}
key: "[[{key}]]"
tags:  # Tags field is included but left empty
---

## Bibliography
{", ".join(authors_list)}. ({year}). _{title}_. {publisher}. {"https://doi.org/" + doi if doi else url}
"""

    # Save as a Markdown file
    md_filename = os.path.join(OUTPUT_DIR, f"{key}.md")
    with open(md_filename, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content)

print(f"Markdown files created in {OUTPUT_DIR}/")
