# Function to format ordinal numbers (1st, 2nd, 3rd, etc.)
def ordinal(n):
    return f"{n}{'st' if n == 1 else 'nd' if n == 2 else 'rd' if n == 3 else 'th'}"

for entry in bib_database.entries:
    key = entry.get("ID", "unknown_key")
    
    # Get title, replace colons with hyphens, and remove line breaks
    title = entry.get("title", "Untitled").replace(":", " - ")
    title = " ".join(title.splitlines())

    year = entry.get("year", "Unknown Year")
    
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
