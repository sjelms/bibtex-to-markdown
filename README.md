# bibtex-to-markdown

A Python-based utility for converting BibTeX entries into Markdown notes compatible with Obsidian, Pandoc, and reference-based workflows.

---

## 📌 Intent

This tool automates the process of transforming academic references from a BibTeX `.bib` file into individual Markdown notes. Each note is formatted for compatibility with:
- [Pandoc](https://pandoc.org) citation processing (`[@citation_key]`)
- Obsidian-style `[[wikilinks]]` for internal navigation
- Markdown-based academic writing workflows

---

## ⚙️ Actions

The script performs the following actions:

- Parses a BibTeX file using `bibtexparser`
- Cleans and formats metadata including author names, titles, and keywords
- Creates one Markdown file per BibTeX entry
- Adds both a Pandoc-style filename (e.g., `@Smith2020-ab.md`) and Obsidian-style link in the frontmatter (`[[Smith2020-ab]]`)
- Inserts a Chicago-style bibliography block and optional abstract into each file
- Adds YAML `aliases` for citations (Full Title Case and optional Short Title Case)
- Generates author pages with YAML `aliases` (surname) and a Map of Content (MOC) using `[[@key|Short Title]]`

---

## 📥 Input

- A valid `.bib` file (BibTeX format), such as `main.bib`
- BibTeX keys must be unique
- Optional fields supported: `author`, `title`, `journal`, `publisher`, `url`, `year`, `abstract`, `keywords`, `institution`

---

## 📤 Output

- A folder called `markdown_entries/` (if not present, it is created)
- Inside this folder:
  - Individual Markdown files named using the format: `@BibTeXKey.md`
  - Each file includes:
    - YAML frontmatter with:
      - Title, year
      - Authors (with Obsidian-style links `[[Author Name]]`)
      - Key (in format `[[@BibTeXKey]]`)
      - Aliases (full title and optional short title)
      - Optional fields: institution, journal, publisher (all as Obsidian links)
      - Tags (from keywords)
    - Optional abstract
    - Chicago-style bibliography section
    - Pandoc-compatible filename for citation use (`[@BibTeXKey]`)

- A folder called `authors/`:
  - Individual Markdown files per author with:
    - YAML frontmatter including:
      - `author`: `"[[First Last]]"`
      - `aliases`: surname (for quick `[[Surname]]` links)
      - optional: `institution`, `field`, `type`
    - Heading with author name
    - `### Content:` section with MOC links of the form `[[@CitationKey|Short Title]]`
    - `#### Bibliography:` with embedded transclusions `![[@CitationKey]]`

---

## 🧱 Framework

- **Python 3.7+**
- Dependencies:
  - `bibtexparser`
  - Standard libraries: `os`, `re`

Ensure dependencies are installed:
```bash
pip install bibtexparser
```

Run the script:
```bash
python convert_bibtex.py
```

---

## ✨ Example

Citation file (`markdown_entries/@Doyle1892-fj.md`):
```markdown
---
title: The Adventures of Sherlock Holmes
year: 1892
author - 1: "[[Arthur Conan Doyle]]"
key: "[[@Doyle1892-fj]]"
aliases:
  - The Adventures Of Sherlock Holmes
publisher: "[[George Newnes Ltd]]"
tags:
  - EPubs-Books
  - _BibTex-to-MD-Git
  - ePub
---

> [!bibliography]
> Doyle, Arthur Conan. 1892. “The Adventures of Sherlock Holmes.” "[[George Newnes Ltd]]"
```

Author file (`authors/Arthur Conan Doyle.md`):
```markdown
---
author: "Arthur Conan Doyle"
institution:
field:
type:
aliases:
  - Doyle
---

## Arthur Conan Doyle

### Content:
[[@Doyle1892-fj|The Adventures Of Sherlock Holmes]]

#### Bibliography:

![[@Doyle1892-fj]]
```

---

## 🛠️ Troubleshooting

### 🟥 Problem: Filenames or links are not resolving in Obsidian  
✅ Check that the Markdown files are stored within your Obsidian vault  
✅ Ensure filenames use the `@BibTeXKey` format if linking via Pandoc citation syntax  
✅ Use `[[@BibTeXKey]]` or `[@BibTeXKey]` depending on purpose

### 🟥 Problem: Non-Latin characters or accents appear incorrectly  
✅ Text cleaning is applied, but additional edge cases can be adjusted in `clean_text()` or `format_authors()`

### 🟥 Problem: Markdown files overwrite each other  
✅ BibTeX keys must be unique; conflicts will silently overwrite existing files

---

For enhancements or bug reports, please open an issue in the GitHub repository. [https://github.com/sjelms/bibtex-to-markdown](https://github.com/sjelms/bibtex-to-markdown)
