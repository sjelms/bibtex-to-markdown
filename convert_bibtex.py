import os
import re
import argparse
import bibtexparser

# Define file paths
BIBTEX_FILE = "main.bib"
OUTPUT_DIR = "titles"
AUTHORS_DIR = "authors"
PUBLISHERS_DIR = "publisher"

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(AUTHORS_DIR, exist_ok=True)
os.makedirs(PUBLISHERS_DIR, exist_ok=True)

# Dictionary to track authors and their metadata
author_metadata = {}  # Will store citations, institutions, and other fields
entity_metadata = {}  # Will store publisher/journal pages and their citations

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


def normalize_entity_name(text: str) -> str:
    """Normalize publisher/journal names for links and filenames.
    - Remove braces/newlines via clean_text
    - Remove punctuation (.,;:!-'"/&()[]{}-_ and slashes)
    - Remove underscores
    - Collapse multiple spaces
    - Trim
    """
    if not text:
        return ""
    t = clean_text(text, is_yaml=True)
    # Remove common punctuation and symbols
    t = re.sub(r"[\._,;:!\-–—'\"/&()\[\]{}\\]", " ", t)
    # Remove underscores explicitly (in case left by \w)
    t = t.replace("_", " ")
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t)
    return t.strip()


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

parser = argparse.ArgumentParser(description="Convert BibTeX to Markdown with YAML frontmatter.")
parser.add_argument(
    "--only-with-editors",
    action="store_true",
    help="Process only entries that have an 'editor' field."
)
parser.add_argument(
    "--update-frontmatter-only",
    action="store_true",
    help="Replace only the YAML frontmatter in existing files; preserve body content."
)
parser.add_argument(
    "--no-author-files",
    action="store_true",
    help="Do not regenerate per-author files (useful for partial updates)."
)
args = parser.parse_args()

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
processed_count = 0
for entry in bib_database.entries:
    # Optionally restrict to entries that include editors
    if args.only_with_editors and not entry.get("editor"):
        continue
    key = entry.get("ID", "unknown_key")
    raw_title = entry.get("title", "Untitled")
    title = clean_text(raw_title, is_yaml=True)
    year = entry.get("year", "Unknown Year")

    # Process authors (supports 'editor' as fallback for author field)
    raw_authors = entry.get("author", entry.get("editor", "Unknown Author"))
    formatted_authors = format_authors(raw_authors)

    # Process editors separately; include only if present
    raw_editors = entry.get("editor")
    formatted_editors = format_authors(raw_editors) if raw_editors else []

    # Get other fields and wrap them in [[ ]] and QUOTES, only if they exist
    institution = f'"[[{clean_text(entry.get("institution", ""), is_yaml=True)}]]"' if entry.get("institution") and entry.get("institution").strip() else None
    # Normalize publisher/journal names for linking and filenames
    raw_publisher = entry.get("publisher", "")
    raw_journal = entry.get("journal", "")
    norm_publisher = normalize_entity_name(raw_publisher) if raw_publisher and raw_publisher.strip() else ""
    norm_journal = normalize_entity_name(raw_journal) if raw_journal and raw_journal.strip() else ""
    publisher = f'"[[{norm_publisher}]]"' if norm_publisher else None
    journal = f'"[[{norm_journal}]]"' if norm_journal else None

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

    # Add editors to YAML if present
    if formatted_editors:
        for i, editor in enumerate(formatted_editors, start=1):
            yaml_lines.append(f'editor - {i}: "{editor}"')

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

    # Save or update the Markdown file
    md_filename = os.path.join(OUTPUT_DIR, f"@{key}.md")
    new_frontmatter = "\n".join(yaml_lines)  # includes opening and closing --- lines
    if args.update_frontmatter_only and os.path.exists(md_filename):
        # Replace only the frontmatter block; preserve the body
        with open(md_filename, "r", encoding="utf-8") as md_file:
            existing = md_file.read()

        # Match first frontmatter block and replace
        fm_pattern = re.compile(r"^---\n.*?\n---", re.DOTALL | re.MULTILINE)
        if fm_pattern.search(existing):
            updated = fm_pattern.sub(new_frontmatter, existing, count=1)
        else:
            # If no existing frontmatter, prepend it
            updated = new_frontmatter + "\n\n" + existing

        with open(md_filename, "w", encoding="utf-8") as md_file:
            md_file.write(updated.strip())
    else:
        # Write full content (frontmatter + generated sections)
        with open(md_filename, "w", encoding="utf-8") as md_file:
            md_file.write(markdown_content.strip())

    processed_count += 1
    
    # Track citations and metadata for each author (include editors too)
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

    # Also create pages for editors (so all [[names]] have files)
    for editor in formatted_editors:
        clean_editor = editor.replace("[[", "").replace("]]", "")
        if clean_editor not in author_metadata:
            author_metadata[clean_editor] = {
                'citations': [],
                'institutions': set(),
                'fields': set(),
                'moc_display': {}
            }
        author_metadata[clean_editor]['citations'].append(key)
        author_metadata[clean_editor]['moc_display'][key] = display_alias

    # Track publisher/journal entity pages
    def ensure_entity(name: str, category: str):
        if not name:
            return
        if name not in entity_metadata:
            entity_metadata[name] = {
                'categories': set(),
                'citations': [],
                'moc_display': {}
            }
        entity_metadata[name]['categories'].add(category)
        entity_metadata[name]['citations'].append(key)
        entity_metadata[name]['moc_display'][key] = display_alias

    if norm_publisher:
        ensure_entity(norm_publisher, 'publisher')
    if norm_journal:
        ensure_entity(norm_journal, 'journal')

# Generate author files (skip if doing a targeted update unless explicitly requested)
if not args.only_with_editors and not args.no_author_files:
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

    # Close frontmatter and add content sections
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
    author_yaml.extend([
        "",
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

# Generate publisher/journal entity files (full runs only by default)
if not args.only_with_editors and not args.no_author_files:
    for name, metadata in entity_metadata.items():
        categories = sorted(list(metadata['categories']))
        fm = [
            "---",
            f"name: {name}",
            "aliases:",
            "see also:",
            "tags:",
            "category:",
        ]
        for c in categories:
            fm.append(f"  - {c}")
        fm.append("---")

        body = [
            "",
            f"## {name}",
            "",
            "### Content:",
        ]
        for citation in sorted(metadata['citations']):
            disp = metadata['moc_display'].get(citation, citation)
            body.append(f"[[@{citation}|{disp}]]")

        content = "\n".join(fm + body)
        filename = os.path.join(PUBLISHERS_DIR, f"{name}.md")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

print(f"✅ Processed {processed_count} entries into {OUTPUT_DIR}/")
if not args.only_with_editors and not args.no_author_files:
    print(f"✅ Author files created in {AUTHORS_DIR}/")
    print(f"✅ Publisher/Journal files created in {PUBLISHERS_DIR}/")
