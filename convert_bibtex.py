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

# Function to clean up text (removes braces, ensures correct formatting)
def clean_text(text):
    if not text:
        return ""
    text = text.strip()
    text = text.replace("\n", " ")  # Ensure multiline text is on a single line
    text = re.sub(r"\{(.*?)\}", r"\1", text)  # Remove braces `{}` while preserving content
    text = text.replace(":", " - ")  # Replace colons with hyphens
    return text.strip()

# Function to properly format author/editor names while keeping institutions together
def format_authors(raw_authors):
    if not raw_authors:
        return ["Unknown Author"]

    # Identify institutional names inside braces and keep them together
    protected_authors = re.findall(r"\{.*?\}", raw_authors)  # Find all `{}` enclosed text
    temp_replacement = "UNIQUE_PLACEHOLDER"
    temp_authors = re.sub(r"\{.*?\}", temp_replacement, raw_authors)  # Temporarily replace institutions

    # Split on `and` now that institutions are protected
    authors_list = [author.strip() for author in temp_authors.split(" and ")]

    # Replace placeholders back with institution names
    for i, author in enumerate(authors_list):
        if temp_replacement in author:
            authors_list[i] = protected_authors.pop(0)

    formatted_authors = []
    for name in authors_list:
        name = clean_text(name)  # Remove `{}` after protecting institutions
        name_parts = name.split(", ")
        if len(name_parts) == 2:  # Standard "Last, First" format
            formatted_authors.append(f"{name_parts[1]} {name_parts[0]}")
        else:
            formatted_authors.append(name)  # Institutions remain unchanged

    return formatted_authors

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

    # Get other fields
    institution = clean_text(entry.get("institution", ""))
    affiliation = clean_text(entry.get("affiliation", ""))
    publisher = clean_text(entry.get("publisher", ""))
    url = clean_text(entry.get("url", ""))

    # Format bibliography
    bibliography = format_chicago_bibliography(formatted_authors, year, title, publisher, url)

    # Ensure Correct YAML Formatting
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
    yaml_lines.append("---")

    # Final Markdown output
    markdown_content = "\n".join(yaml_lines) + f"\n\n## Bibliography\n{bibliography}"

    # Save the Markdown file
    md_filename = os.path.join(OUTPUT_DIR, f"{key}.md")
    with open(md_filename, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content.strip())

print(f"✅ Markdown files successfully created in {OUTPUT_DIR}/")
