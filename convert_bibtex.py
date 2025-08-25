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
def clean_text(text, is_yaml=False):
    if not text:
        return ""
    
    text = text.strip()
    text = text.replace("\n", " ")  # Ensure multiline text is on a single line
    
    # Handle escaped characters
    if is_yaml:
        # For YAML content, handle escaped characters differently
        text = re.sub(r'\\&', 'and', text)  # Replace \& with 'and'
        text = re.sub(r'\\_', '_', text)     # Remove escape from underscore
        text = re.sub(r'\\([^&_])', r'\1', text)  # Remove other escapes but keep the character
    else:
        # For non-YAML content (like abstracts), preserve the original characters
        text = text.replace('\\&', '&')
        text = text.replace('\\_', '_')
        
    text = re.sub(r"\{(.*?)\}", r"\1", text)  # Remove braces `{}` while preserving content
    text = text.replace(":", " - ")  # Replace colons with hyphens
    
    if is_yaml:
        text = text.replace("&", "and")  # Replace unescaped ampersands with "and" in YAML
        
    return text.strip()

# Function to correctly parse authors while keeping institutions together
def format_authors(raw_authors):
    if not raw_authors:
        return ["Unknown Author"]

    # Clean up newlines and extra spaces in the raw authors string
    raw_authors = " ".join(raw_authors.split())

    # Identify institutions inside `{}` and preserve them
    protected_authors = re.findall(r"\{.*?\}", raw_authors)  # Find `{}` enclosed text
    temp_replacement = "INSTITUTION_PLACEHOLDER"
    temp_authors = re.sub(r"\{.*?\}", temp_replacement, raw_authors)  # Temporarily replace institutions

    # Split on ` and ` that is outside `{}` to separate personal names
    authors_list = []
    for author in temp_authors.split(" and "):
        author = author.strip()
        # If author contains multiple names (like "Hastak, Makarand and LaScola Needy, Kim")
        if " and " in author.lower():  # Case insensitive check
            # Split these into separate authors
            sub_authors = [a.strip() for a in author.split(" and ")]
            authors_list.extend(sub_authors)
        else:
            authors_list.append(author)

    # Restore institution names in their correct positions
    for i, author in enumerate(authors_list):
        if temp_replacement in author:
            authors_list[i] = protected_authors.pop(0)

    formatted_authors = []
    for name in authors_list:
        name = clean_text(name)  # Remove `{}` after processing

        # Handle author names in "Last, First" format
        if "," in name and not name.startswith("{"):
            name_parts = name.split(", ")
            if len(name_parts) == 2:
                formatted_authors.append(f"[[{name_parts[1]} {name_parts[0]}]]")
            else:
                formatted_authors.append(f"[[{name}]]")  # Keep institutions unchanged
        else:
            formatted_authors.append(f"[[{name}]]")  # Keep as is if no comma found

    return formatted_authors

# Function to format bibliography in Chicago 17th Edition
def format_chicago_bibliography(authors, year, title, publisher, url):
    # Remove brackets before formatting the bibliography
    authors = [author.replace("[[", "").replace("]]", "") for author in authors]

    first_author = authors[0].split(" ")
    if len(first_author) > 1:
        first_author = f"{first_author[-1]}, {' '.join(first_author[:-1])}"  # Convert first author to "Last, First"
    else:
        first_author = authors[0]  # Keep institutions unchanged

    formatted_authors = [first_author] + authors[1:]  # Keep others as "First Last"
    bibliography = f'{", ".join(formatted_authors)}. {year}. “{title}.” {publisher if publisher else ""}. {url}'
    return bibliography.strip().rstrip(".")  # Remove trailing period

# Function to process keywords into valid YAML tags
def process_keywords(keyword_str):
    if not keyword_str:
        return []
    keywords = keyword_str.replace("\\", "").split(";")
    cleaned_keywords = []
    for kw in keywords:
        kw = clean_text(kw)  # Apply the clean_text function
        kw = re.sub(r"[+]", "", kw)  # Remove plus signs (`+`)
        kw = re.sub(r"(\.\d+)", "", kw)  # Remove decimal numbers (e.g., "4.0" → "4")
        kw = re.sub(r"[\(\)\[\]\{\}]", "", kw)  # Remove parentheses, brackets, and curly braces
        kw = re.sub(r"\s+", "-", kw)  # Replace spaces with hyphens
        kw = kw.rstrip("-")  # Remove trailing hyphens
        if kw:
            cleaned_keywords.append(kw)
    return cleaned_keywords

# Process each entry in BibTeX
for entry in bib_database.entries:
    key = entry.get("ID", "unknown_key")
    title = clean_text(entry.get("title", "Untitled"), is_yaml=True)
    year = entry.get("year", "Unknown Year")

    # Process authors (supports 'editor' as fallback)
    raw_authors = entry.get("author", entry.get("editor", "Unknown Author"))
    formatted_authors = format_authors(raw_authors)

    # Get other fields and wrap them in [[ ]] and QUOTES, only if they exist
    institution = f'"[[{clean_text(entry.get("institution", ""), is_yaml=True)}]]"' if entry.get("institution") and entry.get("institution").strip() else None
    publisher = f'"[[{clean_text(entry.get("publisher", ""), is_yaml=True)}]]"' if entry.get("publisher") and entry.get("publisher").strip() else None
    journal = f'"[[{clean_text(entry.get("journal", ""), is_yaml=True)}]]"' if entry.get("journal") and entry.get("journal").strip() else None

    # Process keywords into valid YAML tags
    keyword_tags = process_keywords(entry.get("keywords", ""))

    # Extract abstract and clean it (not YAML, so preserve original characters)
    abstract = clean_text(entry.get("abstract", ""), is_yaml=False)

    # Format bibliography
    bibliography = format_chicago_bibliography(formatted_authors, year, title, publisher, entry.get("url", ""))

    # Ensure Correct YAML Formatting
    yaml_lines = [
        "---",
        f"title: {title}",
        f"year: {year}",
    ]

    for i, author in enumerate(formatted_authors, start=1):
        yaml_lines.append(f'author - {i}: "{author}"')

    yaml_lines.append(f'key: "[[@{key}]]"')

    # Only add non-None fields
    if institution is not None:
        yaml_lines.append(f"institution: {institution}")
    if journal is not None:
        yaml_lines.append(f"journal: {journal}")
    if publisher is not None:
        yaml_lines.append(f"publisher: {publisher}")

    yaml_lines.append("tags:")
    for tag in keyword_tags:
        yaml_lines.append(f"  - {tag}")

    yaml_lines.append("---")

    # Assemble final Markdown content
    markdown_content = "\n".join(yaml_lines) + f"\n\n> [!Bibliography]\n> {bibliography}"

    # Add abstract section if available
    if abstract:
        markdown_content += f"\n\n## Abstract\n{abstract}"

    # Save the Markdown file
    md_filename = os.path.join(OUTPUT_DIR, f"@{key}.md")
    with open(md_filename, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content.strip())

print(f"✅ Markdown files successfully created in {OUTPUT_DIR}/")
