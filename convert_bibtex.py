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

# Function to clean up text (removing braces and ensuring proper formatting)
def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"\{(.*?)\}", r"\1", text)  # Remove all {braces}
    text = text.replace(":", " - ")  # Replace colons with hyphens
    text = " ".join(text.split())  # Remove unintended line breaks
    return text.strip()

# Function to properly format author names
def format_authors(raw_authors):
    if not raw_authors:
        return ["Unknown Author"]

    authors_list = raw_authors.split(" and ")
    formatted_authors = []
    
    for name in authors_list:
        name = clean_text(name)
        name_parts = name.split(", ")
        if len(name_parts) == 2:
            formatted_authors.append(f"{name_parts[1]} {name_parts[0]}")
        else:
            formatted_authors.append(name)

    return formatted_authors

# Function to process keywords into YAML-friendly tags
def process_keywords(keyword_str):
    if not keyword_str:
        return []
    keywords = keyword_str.replace("\\", "").split(";")
    cleaned_keywords = []
    for kw in keywords:
        kw = clean_text(kw)  # Apply the clean_text function
        kw = re.sub(r"[+]", "", kw)  # Remove plus signs (`+`)
        kw = re.sub(r"(\.\d+)", "", kw)  # Remove decimal numbers (e.g., "4.0" → "4")
        kw = re.sub(r"\s+", "-", kw)  # Replace spaces with hyphens
        kw = kw.rstrip("-")  # Remove trailing hyphens
        if kw:
            cleaned_keywords.append(kw)
    return cleaned_keywords

# Function to format bibliography in Chicago 17th Edition
def format_chicago_bibliography(authors, year, title, publisher, url):
    formatted_authors = ", ".join(authors[:-1]) + ", and " + authors[-1] if len(authors) > 1 else authors[0]
    bibliography = f'{formatted_authors}. {year}. “{title}.” {publisher if publisher else ""}. {url}'
    return bibliography.strip().rstrip(".")  # Remove trailing period

# Process each entry in BibTeX
for entry in bib_database.entries:
    key = entry.get("ID", "unknown_key")
    title = clean_text(entry.get("title", "Untitled"))
    year = entry.get("year", "Unknown Year")

    # Process authors (supports 'editor' as fallback)
    raw_authors = entry.get("author", entry.get("editor", "Unknown Author"))
    formatted_authors = format_authors(raw_authors)

    # Remove `{}` from institution & affiliation
    institution = clean_text(entry.get("institution", ""))
    affiliation = clean_text(entry.get("affiliation", ""))

    # Get other fields
    publisher = clean_text(entry.get("publisher", ""))
    url = clean_text(entry.get("url", ""))
    
    # Process keywords into valid YAML tags
    keyword_tags = process_keywords(entry.get("keywords", ""))

    # Format bibliography
    bibliography = format_chicago_bibliography(formatted_authors, year, title, publisher, url)

    # **Ensure Correct YAML Formatting**
    yaml_lines = [
        "---",
        f"title: {title}",
        f"year: {year}",
    ]

    for i, author in enumerate(formatted_authors, start=1):
        yaml_lines.append(f'author - {i}: "{author}"')

    yaml_lines.append(f'key: "[[{key}]]"')

    if institution:
        yaml_lines.append(f"institution: {institution}")
    if affiliation:
        yaml_lines.append(f"affiliation: {affiliation}")

    yaml_lines.append("tags:")
    for tag in keyword_tags:
        yaml_lines.append(f"  - {tag}")

    yaml_lines.append("---")

    # Final Markdown output
    markdown_content = "\n".join(yaml_lines) + f"\n\n## Bibliography\n{bibliography}"

    # Save the Markdown file
    md_filename = os.path.join(OUTPUT_DIR, f"{key}.md")
    with open(md_filename, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content.strip())

print(f"✅ Markdown files successfully created in {OUTPUT_DIR}/")
