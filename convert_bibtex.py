import os
import re
import argparse
from collections import defaultdict
from datetime import datetime
from pybtex.database import parse_file
import latexcodec

def latex_to_unicode(text):
    """Convert LaTeX encoded text to Unicode using latexcodec."""
    if not text:
        return ""
    try:
        # Convert string to bytes, then decode using latex+utf8 codec
        return str(text).encode("utf-8").decode('latex+utf8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        # Fallback to original text if decoding fails
        return str(text)

# Define file paths
BIBTEX_FILE = "main.bib"
OUTPUT_DIR = "titles"
AUTHORS_DIR = "authors"
PUBLISHERS_DIR = "publisher"
TYPES_DIR = "type"

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(AUTHORS_DIR, exist_ok=True)
os.makedirs(PUBLISHERS_DIR, exist_ok=True)
os.makedirs(TYPES_DIR, exist_ok=True)

# Dictionary to track authors and their metadata
author_metadata = {}  # Will store citations, institutions, and other fields
entity_metadata = {}  # Will store publisher/journal pages and their citations
type_metadata = defaultdict(list)  # Will store entries grouped by BibLaTeX entry type

MONTH_MAP = {
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}


def get_field(fields, *names, default=""):
    """Return the first non-empty field value among names."""
    for n in names:
        value = fields.get(n)
        if value:
            return value
    return default


def normalize_month(value):
    """Convert BibLaTeX month formats (textual or numeric) to MM."""
    if not value:
        return ""
    value = value.strip()
    lower = value.lower()
    if lower in MONTH_MAP:
        return MONTH_MAP[lower]
    if lower.isdigit():
        return lower.zfill(2)
    # BibLaTeX may wrap the month in braces or quotes
    cleaned = re.sub(r"[{}]", "", value)
    if cleaned.lower() in MONTH_MAP:
        return MONTH_MAP[cleaned.lower()]
    if cleaned.isdigit():
        return cleaned.zfill(2)
    return ""


def get_iso_date(fields):
    """
    Prefer the BibLaTeX 'date' field (YYYY, YYYY-MM, YYYY-MM-DD).
    Fallback to 'year' + optional 'month'/'day'.
    """
    date_value = fields.get("date")
    if date_value:
        return date_value

    year = fields.get("year")
    if not year:
        return ""
    month = normalize_month(fields.get("month", ""))
    day = fields.get("day")
    day_str = ""
    if day and str(day).isdigit():
        day_str = str(day).zfill(2)

    if month and day_str:
        return f"{year}-{month}-{day_str}"
    if month:
        return f"{year}-{month}"
    return str(year)

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

# Load the BibLaTeX/BibTeX database
bib_data = parse_file(BIBTEX_FILE)

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
    
    if is_yaml:
        text = text.replace(":", " - ")  # Replace colons with hyphens for YAML safety
        text = text.replace("&", "and")  # Replace unescaped ampersands with "and" in YAML
    
    return text.strip()

def format_persons(persons):
    """Convert pybtex Person objects to Obsidian-style wiki links."""
    if not persons:
        return []

    formatted = []
    for person in persons:
        first_parts = person.first_names + person.middle_names + person.prelast_names
        last_parts = person.last_names
        lineage_parts = person.lineage_names

        first = " ".join(latex_to_unicode(part) for part in first_parts if part).strip()
        last = " ".join(latex_to_unicode(part) for part in last_parts if part).strip()
        lineage = " ".join(latex_to_unicode(part) for part in lineage_parts if part).strip()

        name_fragments = [fragment for fragment in (first, last, lineage) if fragment]
        if name_fragments:
            name = " ".join(name_fragments)
        else:
            text = latex_to_unicode(person.text or "").strip()
            name = text if text else "Unknown Author"

        # Remove lingering braces and collapse whitespace
        name = re.sub(r"[{}]", "", name)
        name = re.sub(r"\s+", " ", name).strip()
        formatted.append(f"[[{name or 'Unknown Author'}]]")

    return formatted

# Function to format bibliography in Chicago 17th Edition
def format_chicago_bibliography(authors, year, title, publisher, url):
    # Remove brackets before formatting the bibliography
    authors = [author.replace("[[", "").replace("]]", "") for author in authors]
    display_title = clean_text(title, is_yaml=False)

    first_author = authors[0].split(" ")
    if len(first_author) > 1:
        first_author = f"{first_author[-1]}, {' '.join(first_author[:-1])}"  # Convert first author to "Last, First"
    else:
        first_author = authors[0]  # Keep institutions unchanged

    formatted_authors = [first_author] + authors[1:]  # Keep others as "First Last"
    bibliography = f'{", ".join(formatted_authors)}. {year}. “{display_title}.” {publisher if publisher else ""}. {url}'
    return bibliography.strip().rstrip(".")  # Remove trailing period

# Function to process keywords into valid YAML tags
def process_keywords(keyword_str):
    if not keyword_str:
        return []
    # Remove escape slashes that often appear in BibLaTeX keyword exports
    sanitized = keyword_str.replace("\\", "")
    # BibLaTeX commonly separates keywords with commas or semicolons; handle both
    keywords = re.split(r"[;,]", sanitized)
    cleaned_keywords = []
    for kw in keywords:
        kw = kw.strip()
        if not kw:
            continue

        # Clean the keyword while preserving punctuation needed for slugs
        kw = clean_text(kw, is_yaml=True)
        kw = kw.replace("+", " plus ")   # Preserve meaning of '+' while keeping YAML safe
        kw = kw.replace("/", " ")        # Treat slashes as separators
        kw = kw.replace(".", " ")        # Avoid collapsing decimal digits (e.g., 4.0 -> 4-0 later)
        kw = re.sub(r"[\(\)\[\]\{\}]", "", kw)  # Remove brackets
        kw = re.sub(r"\s+", "-", kw)  # Replace whitespace runs with hyphens
        kw = re.sub(r"-+", "-", kw).strip("-")  # Collapse multiple hyphens
        if kw:
            cleaned_keywords.append(kw)
    return cleaned_keywords

# Process each entry in BibLaTeX/BibTeX source
processed_count = 0
for key, entry in bib_data.entries.items():
    fields = entry.fields

    authors_persons = entry.persons.get("author", [])
    editors_persons = entry.persons.get("editor", [])

    # Optionally restrict to entries that include editors
    if args.only_with_editors and not editors_persons:
        continue

    raw_title_value = latex_to_unicode(get_field(fields, "title", "maintitle") or "Untitled")
    title = clean_text(raw_title_value, is_yaml=True)
    raw_booktitle_value = latex_to_unicode(get_field(fields, "booktitle"))
    booktitle = clean_text(raw_booktitle_value, is_yaml=True) if raw_booktitle_value else ""
    iso_date = get_iso_date(fields)
    year_value = fields.get("year")
    year = str(year_value) if year_value else (iso_date[:4] if iso_date else "Unknown Year")
    year = re.sub(r"[{}]", "", year).strip()
    entry_type = entry.type.lower() if entry.type else ""
    entry_type = re.sub(r"[{}]", "", entry_type).strip()

    # Process authors (supports 'editor' as fallback for author field)
    formatted_authors = format_persons(authors_persons)
    if not formatted_authors:
        formatted_authors = format_persons(editors_persons)
    if not formatted_authors:
        formatted_authors = ["[[Unknown Author]]"]

    # Process editors separately; include only if present
    formatted_editors = format_persons(editors_persons)

    # Get other fields and wrap them in [[ ]] and quotes, only if they exist
    raw_institution = latex_to_unicode(get_field(fields, "institution", "organization"))
    institution_clean = clean_text(raw_institution, is_yaml=True) if raw_institution else ""
    institution_link = f"[[{institution_clean}]]" if institution_clean else ""
    institution = f'"{institution_link}"' if institution_link else None

    raw_publisher = latex_to_unicode(get_field(fields, "publisher"))
    raw_journal = latex_to_unicode(get_field(fields, "journaltitle", "journal"))
    norm_publisher = normalize_entity_name(raw_publisher) if raw_publisher else ""
    norm_journal = normalize_entity_name(raw_journal) if raw_journal else ""
    publisher_link = f"[[{norm_publisher}]]" if norm_publisher else ""
    journal_link = f"[[{norm_journal}]]" if norm_journal else ""
    publisher = f'"{publisher_link}"' if publisher_link else None
    journal = f'"{journal_link}"' if journal_link else None

    # Process keywords into valid YAML tags
    keyword_tags = process_keywords(latex_to_unicode(get_field(fields, "keywords")))

    # Extract abstract and clean it (not YAML, so preserve original characters)
    abstract_raw = latex_to_unicode(get_field(fields, "abstract"))
    abstract = clean_text(abstract_raw, is_yaml=False)

    # Choose publisher/journal/institution for bibliography display
    bibliography_source = ""
    if publisher_link:
        bibliography_source = publisher_link
    elif journal_link:
        bibliography_source = journal_link
    elif institution_link:
        bibliography_source = institution_link

    url = get_field(fields, "url")
    doi = get_field(fields, "doi")
    if not url and doi:
        url = f"https://doi.org/{doi}"

    bibliography = format_chicago_bibliography(
        formatted_authors,
        year,
        raw_title_value,
        bibliography_source,
        url or "",
    )

    # Build title aliases for citation YAML
    title_aliases = extract_title_aliases(raw_title_value)
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
    if booktitle:
        yaml_lines.append(f"booktitle: {booktitle}")

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

    if entry_type:
        yaml_lines.append(f'type: "[[@{entry_type}]]"')

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
                'moc_display': {}
            }
        if key not in author_metadata[clean_author]['citations']:
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
                'moc_display': {}
            }
        if key not in author_metadata[clean_editor]['citations']:
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
        if key not in entity_metadata[name]['citations']:
            entity_metadata[name]['citations'].append(key)
        entity_metadata[name]['moc_display'][key] = display_alias

    if norm_publisher:
        ensure_entity(norm_publisher, 'publisher')
    if norm_journal:
        ensure_entity(norm_journal, 'journal')

    # Track entries per BibLaTeX type for directory generation
    if entry_type:
        primary_author_for_sort = formatted_authors[0].replace("[[", "").replace("]]", "") if formatted_authors else "Unknown Author"
        year_int = int(year) if year.isdigit() and len(year) == 4 else None
        type_metadata[entry_type].append({
            'key': key,
            'display_alias_short': display_alias,
            'display_alias_long': title_aliases[0] if title_aliases else title,
            'sort_author': primary_author_for_sort,
            'year': year,
            'year_int': year_int,
        })

# Generate author files (skip if doing a targeted update unless explicitly requested)
if not args.only_with_editors and not args.no_author_files:
    for author, metadata in author_metadata.items():
        # Create author file content
        author_yaml = [
            "---",
            f'author: "{author}"'  # author already has [[ ]] from format_persons()
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
        for citation in sorted(set(metadata['citations'])):
            disp = metadata['moc_display'].get(citation, citation)
            author_yaml.append(f"[[@{citation}|{disp}]]")
        author_yaml.extend([
            "",
            "#### Bibliography:",
            ""  # Empty line before citations for better readability
        ])

        # Add citation embeds, one per line
        for citation in sorted(set(metadata['citations'])):
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

    # Generate type-based directory files
    timestamp = datetime.now().isoformat(timespec="seconds")
    for entry_type, entries in type_metadata.items():
        if not entries:
            continue

        decade_map = defaultdict(lambda: defaultdict(list))
        unknown_year_entries = []

        for item in entries:
            if item['year_int'] is not None:
                decade_start = (item['year_int'] // 10) * 10
                decade_map[decade_start][item['year_int']].append(item)
            else:
                unknown_year_entries.append(item)

        type_lines = [
            "---",
            f'type: "[[@{entry_type}]]"',
            f"amended: {timestamp}",
            "---",
            "",
            "# Directory",
        ]

        for decade_start in sorted(decade_map.keys(), reverse=True):
            decade_end = decade_start + 9
            type_lines.append(f"## {decade_start}-{decade_end}")
            for year_value in sorted(decade_map[decade_start].keys(), reverse=True):
                type_lines.append(f"### {year_value}")
                entries_for_year = sorted(
                    decade_map[decade_start][year_value],
                    key=lambda e: (e['sort_author'].lower(), (e['display_alias_short'] or "").lower())
                )
                for entry in entries_for_year:
                    display_title = entry['display_alias_long'] or entry['display_alias_short']
                    type_lines.append(f"- [[@{entry['key']}|{display_title}]]")

        if unknown_year_entries:
            type_lines.append("## Unknown Year")
            for entry in sorted(
                unknown_year_entries,
                key=lambda e: (e['sort_author'].lower(), (e['display_alias_short'] or "").lower())
            ):
                display_title = entry['display_alias_long'] or entry['display_alias_short']
                type_lines.append(f"- [[@{entry['key']}|{display_title}]]")

        type_content = "\n".join(type_lines).strip() + "\n"
        type_filename = os.path.join(TYPES_DIR, f"@{entry_type}.md")
        with open(type_filename, "w", encoding="utf-8") as f:
            f.write(type_content)

print(f"✅ Processed {processed_count} entries into {OUTPUT_DIR}/")
if not args.only_with_editors and not args.no_author_files:
    print(f"✅ Author files created in {AUTHORS_DIR}/")
    print(f"✅ Publisher/Journal files created in {PUBLISHERS_DIR}/")
    print(f"✅ Type directories created in {TYPES_DIR}/")
