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

# Function to process keywords into tags
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
        kw = kw.replace(":", "-")  # Remove colons
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
    title = entry.get("title", "Untitled").replace(":", " - ")
    title = re.sub(r"\{(.*?)\}", r"\1", title)  # Remove braces `{}` from title formatting
    title = " ".join(title.splitlines())  # Ensure title is on one line

    year = entry.get("year", "Unknown Year")

    # Processing Authors
    raw_authors = entry.get("author", "Unknown Author")
    authors_list = raw_authors.split(" and ") if raw_authors else []
    
    formatted_authors = []
    for name in authors_list:
        name = re.sub(r"^\{(.*?)\}$", r"\1", name)  # Remove `{}` from institutions
        name_parts = name.split(", ")
        if len(name_parts) == 2:
            formatted_authors.append(f"{name_parts[1]} {name_parts[0]}")
        else:
            formatted_authors.append(name)

    print(f"\nDEBUG: Processed Authors for {key}: {formatted_authors}")  # Print to check formatting

    institution = entry.get("institution", "")
    affiliation = entry.get("affiliation", "")

    print(f"DEBUG: Institution: {institution}")
    print(f"DEBUG: Affiliation: {affiliation}")

    # Debugging YAML Output Before Writing
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
    
    # Process tags and print them for debugging
    keyword_tags = process_keywords(entry.get("keywords", ""))
    for tag in keyword_tags:
        yaml_lines.append(f"  - {tag}")

    yaml_lines.append("---")

    print("\nDEBUG: YAML Output Before Writing:")
    print("\n".join(yaml_lines))

    # Format bibliography
    publisher = entry.get("publisher", "")
    url = entry.get("url", "").strip()
    bibliography = format_chicago_bibliography(formatted_authors, year, title, publisher, url)

    markdown_content = "\n".join(yaml_lines) + f"\n\n## Bibliography\n{bibliography}"

    # Save the Markdown file
    md_filename = os.path.join(OUTPUT_DIR, f"{key}.md")
    with open(md_filename, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content.strip())

print(f"Markdown files created in {OUTPUT_DIR}/")
