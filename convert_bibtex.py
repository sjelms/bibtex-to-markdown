import os
import re
import bibtexparser

# Define file paths
BIBTEX_FILE = "main.bib"
OUTPUT_DIR = "markdown_entries"
AUTHORS_DIR = "authors"

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(AUTHORS_DIR, exist_ok=True)

# Dictionary to track authors and their metadata
author_metadata = {}  # Will store citations, institutions, and other fields

def get_safe_filename(name):
    # Remove wiki-link brackets
    name = name.replace("[[", "").replace("]]", "")
    # Replace various special characters
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Replace multiple underscores with single one
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    return name


def to_title_case(text: str) -> str:
    # Capitalize each word and hyphenated parts (simple Title Case)
    if not text:
        return ""

    def cap(word: str) -> str:
        if not word:
            return word
        return word[0].upper() + word[1:].lower()

    words = re.split(r"\s+", text.strip())
    result = []
    for w in words:
        if re.search(r"[-–—]", w):
            pieces = re.split(r"([-–—])", w)
            new_pieces = []
            for k, p in enumerate(pieces):
                if k % 2 == 0:
                    new_pieces.append(cap(p))
                else:
                    new_pieces.append(p)
            result.append("".join(new_pieces))
        else:
            result.append(cap(w))
    return " ".join(result)


def extract_title_aliases(raw_title: str) -> list:
    """Return list of aliases: [Full Title Case, Optional Short Title Case]"""
    if not raw_title:
        return []
    # Clean braces but keep punctuation; we don't want YAML-specific replacements
    t = raw_title.strip()
    t = re.sub(r"\{(.*?)\}", r"\1", t)
    t = t.replace("\n", " ")
    # Normalize multi-spaces
    t = re.sub(r"\s+", " ", t)

    # Build full alias (convert ":" to " - " for nicer display consistency)
    full_disp = t.replace(":", " - ")
    full_tc = to_title_case(full_disp)

    short_tc = None
    # Prefer split on spaced dash, then colon
    if " - " in full_tc:
        short_tc = full_tc.split(" - ", 1)[0].strip()
    elif ":" in t:
        short_tc = to_title_case(t.split(":", 1)[0].strip())

    aliases = [full_tc]
    if short_tc and short_tc != full_tc:
        aliases.append(short_tc)
    # Deduplicate while preserving order
    seen = set()
    dedup = []
    for a in aliases:
        if a not in seen:
            dedup.append(a)
            seen.add(a)
    return dedup

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
    raw_title = entry.get("title", "Untitled")
    title = clean_text(raw_title, is_yaml=True)
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

    # Build title aliases for citation YAML
    title_aliases = extract_title_aliases(raw_title)
    # Choose display alias for author MOC: prefer short if present
    display_alias = title_aliases[1] if len(title_aliases) > 1 else (title_aliases[0] if title_aliases else title)

    # Ensure Correct YAML Formatting
    yaml_lines = [
        "---",
        f"title: {title}",
        f"year: {year}",
    ]

    for i, author in enumerate(formatted_authors, start=1):
        yaml_lines.append(f'author - {i}: "{author}"')

    yaml_lines.append(f'key: "[[@{key}]]"')

    # Add aliases for the citation: full title and optional short title
    if title_aliases:
        yaml_lines.append("aliases:")
        for a in title_aliases:
            yaml_lines.append(f"  - {a}")

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
    markdown_content = "\n".join(yaml_lines) + f"\n\n> [!bibliography]\n> {bibliography}"

    # Add abstract section if available
    if abstract:
        markdown_content += f"\n\n> [!abstract]\n> {abstract}"

    # Save the Markdown file
    md_filename = os.path.join(OUTPUT_DIR, f"@{key}.md")
    with open(md_filename, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content.strip())
    
    # Track citations and metadata for each author
    for author in formatted_authors:
        clean_author = author.replace("[[", "").replace("]]", "")
        if clean_author not in author_metadata:
            author_metadata[clean_author] = {
                'citations': [],
                'institutions': set(),
                'fields': set(),
                'moc_display': {}
            }
        author_metadata[clean_author]['citations'].append(key)
        author_metadata[clean_author]['moc_display'][key] = display_alias
        
        # Track institution if available
        if institution:
            inst = institution.replace('"[[', '').replace(']]"', '')
            author_metadata[clean_author]['institutions'].add(inst)

# Generate author files
for author, metadata in author_metadata.items():
    # Create author file content
    author_yaml = [
        "---",
        f'author: "{author}"'  # author already has [[ ]] from format_authors()
    ]
    
    # Add institutions if any
    if metadata['institutions']:
        institutions = sorted(list(metadata['institutions']))
        author_yaml.append(f'institution: "{institutions[0]}"')  # Use first institution as primary
    else:
        author_yaml.append("institution:")
        
    # Add other fields
    author_yaml.extend([
        "field:",
        "type:",
        "aliases:",
    ])

    # Add surname as alias (best-effort split on last token)
    clean_author_no_brackets = author.replace("[[", "").replace("]]", "").strip()
    if clean_author_no_brackets:
        parts = clean_author_no_brackets.split()
        surname = parts[-1]
        if surname:
            author_yaml.append(f"  - {surname}")

    # Map of Content section (human-readable links)
    if metadata['citations']:
        author_yaml.extend([
            "---",
            "",
            f"## {author.replace('[[', '').replace(']]', '')}",  # Remove brackets only for heading
            "",
            "### Content:",
        ])
        for citation in sorted(metadata['citations']):
            disp = metadata['moc_display'].get(citation, citation)
            author_yaml.append(f"[[@{citation}|{disp}]]")
        author_yaml.append("")

    author_yaml.extend([
        "---",
        "",
        f"## {author.replace('[[', '').replace(']]', '')}",  # Remove brackets only for heading
        "#### Bibliography:",
        ""  # Empty line before citations for better readability
    ])
    
    # Add citation embeds, one per line
    for citation in sorted(metadata['citations']):
        author_yaml.append(f"![[@{citation}]]")
        author_yaml.append("")  # Add empty line between citations
    
    # Remove trailing empty line
    if author_yaml[-1] == "":
        author_yaml.pop()
    
    # Save the author file
    filename = get_safe_filename(author) + ".md"
    author_filename = os.path.join(AUTHORS_DIR, filename)
    
    with open(author_filename, "w", encoding="utf-8") as author_file:
        author_file.write("\n".join(author_yaml))

print(f"✅ Citation files created in {OUTPUT_DIR}/")
print(f"✅ Author files created in {AUTHORS_DIR}/")
