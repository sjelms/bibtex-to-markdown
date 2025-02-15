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

def clean_text(text):
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    text = re.sub(r"\{(.*?)\}", r"\1", text)  # Remove braces while preserving content
    text = text.replace(":", " - ")  # Replace colons with hyphens
    return text.strip()

def format_authors(raw_authors):
    if not raw_authors:
        return ["Unknown Author"]

    # Split authors, preserving organizations in braces
    authors = re.findall(r'\{[^}]+\}|[^,\s]+(?:\s+[^,\s]+)*(?=\s*(?:and|\Z))', raw_authors)

    formatted_authors = []
    for author in authors:
        author = author.strip()
        if author.startswith('{') and author.endswith('}'):
            # Organization
            formatted_authors.append(f"[[{author[1:-1]}]]")
        else:
            # Individual author
            names = author.split(',')
            if len(names) == 2:
                # Last, First format
                formatted_authors.append(f"[[{names[1].strip()} {names[0].strip()}]]")
            else:
                # First Last format or single name
                formatted_authors.append(f"[[{author}]]")

    return formatted_authors

def format_chicago_bibliography(authors, year, title, institution, url):
    formatted_authors = []
    for author in authors:
        author = author.replace("[[", "").replace("]]", "")
        if ',' in author:
            names = author.split(',')
            formatted_authors.append(f"{names[0].strip()}, {names[1].strip()}")
        else:
            formatted_authors.append(author)

    author_string = ", ".join(formatted_authors)
    bibliography = f'{author_string}. {year}. "{title}." {institution}. {url}'
    return bibliography.strip().rstrip(".")

def format_affiliations(affiliation_str):
    if not affiliation_str:
        return []
    affiliations = [f"[[{clean_text(aff)}]]" for aff in affiliation_str.split(", ")]
    return affiliations

def process_keywords(keyword_str):
    if not keyword_str:
        return []
    keywords = keyword_str.replace("\\", "").split(";")
    cleaned_keywords = []
    for kw in keywords:
        kw = clean_text(kw)
        kw = re.sub(r"[+]", "", kw)  # Remove plus signs
        kw = re.sub(r"(\.\d+)", "", kw)  # Remove decimal numbers
        kw = re.sub(r"\s+", "-", kw)  # Replace spaces with hyphens
        kw = kw.rstrip("-")  # Remove trailing hyphens
        if kw:
            cleaned_keywords.append(kw)
    return cleaned_keywords

# Process each entry in BibTeX
for entry in bib_database.entries:
    try:
        key = entry.get("ID", "unknown_key")
        title = clean_text(entry.get("title", "Untitled"))
        year = entry.get("year", "Unknown Year")

        # Process authors (supports 'editor' as fallback)
        raw_authors = entry.get("author", entry.get("editor", "Unknown Author"))
        formatted_authors = format_authors(raw_authors)

        # Get other fields and wrap them in [[ ]]
        institution = f"[[{clean_text(entry.get('institution', ''))}]]" if entry.get('institution') else ""
        publisher = f"[[{clean_text(entry.get('publisher', ''))}]]" if entry.get('publisher') else ""
        journal = f"[[{clean_text(entry.get('journal', ''))}]]" if entry.get('journal') else ""

        # Process affiliations into separate indexed values
        affiliations = format_affiliations(entry.get("affiliation", ""))

        # Process keywords into valid YAML tags
        keyword_tags = process_keywords(entry.get("keywords", ""))

        # Format bibliography
        bibliography = format_chicago_bibliography(formatted_authors, year, title, institution, entry.get("url", ""))

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
            yaml_lines.append(f'institution: "{institution}"')
        if journal:
            yaml_lines.append(f'journal: "{journal}"')
        if publisher:
            yaml_lines.append(f'publisher: "{publisher}"')

        for i, aff in enumerate(affiliations, start=1):
            yaml_lines.append(f'affiliation - {i}: "{aff}"')

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

        print(f"Processed entry: {key}")

    except Exception as e:
        print(f"Error processing entry {key}: {str(e)}")

print(f"✅ Markdown files successfully created in {OUTPUT_DIR}/")
