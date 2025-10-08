# BibLaTeX to Markdown for Obsidian

[![Convert BibLaTeX to Markdown](https://github.com/sjelms/bibtex-to-markdown/actions/workflows/bibtex-to-md.yml/badge.svg)](https://github.com/sjelms/bibtex-to-markdown/actions/workflows/bibtex-to-md.yml)  &nbsp;  [![PyPI version](https://badge.fury.io/py/bibtexparser.svg)](https://badge.fury.io/py/bibtexparser)

---
## 📌 Intent

This tool automates the process of transforming academic references from a BibLaTeX `.bib` file into individual Markdown notes. Each note is formatted for compatibility with:
- [Pandoc](https://pandoc.org) citation processing (`[@citation_key]`)
- Obsidian-style `[[wikilinks]]` for internal navigation
- Markdown-based academic writing workflows

---
## ⚙️ Actions
### Overview

`bibtex-to-markdown` converts a BibLaTeX (or legacy BibTeX) database into Obsidian-friendly Markdown. The script:
- Parses `main.bib` with `pybtex`, preserving modern BibLaTeX fields like `date`, `journaltitle`, `institution`, and editors.
- Normalizes LaTeX-encoded text to Unicode via `latexcodec`.
- Emits richly linked Markdown notes for each citation (`titles/`), plus auto-generated author/editor maps (`authors/`) and publisher/journal maps (`publisher/`).
- Keeps Pandoc citation syntax (`[@key]`) and Obsidian wiki-links (`[[Name]]`) in sync so the notes feed both academic writing and knowledge base workflows.

The script performs the following actions:

- Creates one Markdown file per BibLaTeX entry
- Adds both a Pandoc-style filename (e.g., `@Smith2020-ab.md`) and Obsidian-style link in the frontmatter (`[[Smith2020-ab]]`)
- Inserts a Chicago-style bibliography block and optional abstract into each file
- Adds YAML `aliases` for citations (Full Title Case and optional Short Title Case)
- Generates author pages with YAML `aliases` (surname) and a Map of Content (MOC) using `[[@key|Short Title]]`

---

## 🧱 Framework Requirements

- Python 3.9+
- Python packages: `pybtex`, `latexcodec`
- A valid BibLaTeX-formatted `.bib` file (default: `main.bib`)

Install the dependencies:

```bash
pip install pybtex latexcodec
```

---

## Usage

Run a full conversion (regenerates citation, author, and publisher files):

```bash
python convert_bibtex.py
```

### Targeted Updates

Use CLI flags to limit the scope of a run:

- `--only-with-editors` — process only entries that include an `editor` field.
- `--update-frontmatter-only` — refresh just the YAML block in existing files, preserving custom note bodies.
- `--no-author-files` — skip regenerating author/publisher maps (useful for quick checks).

Example: refresh YAML for editor-rich entries without touching existing note bodies or MOCs:

```bash
python convert_bibtex.py --only-with-editors --update-frontmatter-only --no-author-files
```

---

## 📤 Output Structure

| Directory | Contents |
| --- | --- |
| `titles/` | One Markdown note per citation (frontmatter + bibliography/abstract callouts). |
| `authors/` | Obsidian MOC pages for each author/editor, linking to every related citation. |
| `publisher/` | Pages for publishers and journals, with grouped citation links. |
| `type/` | Directories grouped by BibLaTeX entry type with decade/year breakdowns of citations. |

The script auto-creates these folders if they do not exist.

---
## ✨ Example
### Citation Note Template (`titles/@Key.md`)

```markdown
---
title: Paper Title
year: 2023
author - 1: "[[Author One]]"
author - 2: "[[Author Two]]"
editor - 1: "[[Editor Name]]"           # Present only when the BibLaTeX entry has editors
key: "[[@Citation-Key]]"
booktitle: Collection Title              # Present only for entries with `booktitle`
aliases:
  - Paper Title
  - Paper                                 # Optional short title (first dash/colon segment)
institution: "[[Institution Name]]"       # Present only when `institution` or `organization` exists
publisher: "[[Publisher Name]]"
journal: "[[Journal Name]]"
type: "[[@article]]"
tags:
  - keyword-one
  - keyword-two
---

> [!bibliography]
> Author One, Author Two, and Editor Name. 2023. “Paper Title.” [[Publisher Name]]. https://doi.org/...

> [!abstract]
> Abstract text (included only when the source entry has `abstract`)
```

Key behaviors:
- Authors fall back to editors when an entry has no explicit `author`.
- `aliases` include the full title in Title Case and a shortened variant when applicable.
- `institution`, `publisher`, and `journal` render as wiki-links; any missing field is omitted.
- DOIs are expanded to URLs when `url` is absent but `doi` is present.

---

## Author Note Template (`authors/Name.md`)

```markdown
---
author: "[[Author Name]]"
institution: "[[Affiliation]]"    # Present when tracked in the source entry
field:
type:
aliases:
  - Surname
---

## Author Name

### Content:
[[@Citation-Key|Display Title]]
[[@Another-Key|Another Title]]

#### Bibliography:

![[@Citation-Key]]
![[@Another-Key]]
```

- `aliases` always include the surname so `[[Surname]]` resolves in Obsidian.
- The “Content” list provides skim-friendly links; embedded `![[...]]` entries render the full bibliography callouts.

---

### Publisher/Journal Template (`publisher/Entity.md`)

```markdown
---
name: Entity Name
aliases:
see also:
tags:
category:
  - publisher
  - journal
---

## Entity Name

### Content:
[[@Citation-Key|Display Title]]
[[@Citation-2|Another Title]]
```

Entity names are normalized (punctuation removed, whitespace collapsed) to produce stable filenames and wiki-links.

---

## Type Directory Template (`type/@type.md`)

```markdown
---
type: "[[@report]]"
amended: 2025-10-08T10:06:00
---

# Directory
## 2020-2029
### 2020
- [[@Autor2020-ol|The Work Of The Future - Building Better Jobs In An Age Of Intelligent Machines]]
- [[@Barua2020-br|The Construction Workforce - Growing Again, But Not Changing Much]]
## 2010-2019
### 2016
- [[@Berger2016-vc|Structural Transformation In The OECD - Digitalisation, Deindustrialisation And The Future Of Work]]
```

- Notes are grouped first by decade, then year, and sorted alphabetically by the primary author within each year.
- The link text always uses the long/full alias; if absent, the short alias is used as a fallback.
- `amended` records the generation timestamp so you can audit when the directory was last refreshed.

---

## Workflow Summary

1. `pybtex` parses `main.bib`, exposing structured entries and person objects.
2. LaTeX-encoded fields are converted to Unicode before YAML sanitization.
3. The converter writes or updates citation notes, then aggregates authors/editors and publishers/journals.
4. After processing all entries it emits author and entity MOCs (unless suppressed with CLI flags) and prints a run summary.

GitHub Actions (`.github/workflows/bibtex-to-md.yml`) runs the converter on pushes, ensuring generated content stays synchronized with the repository.

---

## 🛠️ Troubleshooting & Known Limitations

- **Institutional authors in bibliographies** — the Chicago formatter currently assumes personal names and may output awkward “Last, First” ordering for organizations. Notes still render correctly in YAML and author MOCs.
- **Duplicate backlinks** — author/entity citation lists are stored in simple arrays; running the converter multiple times without pruning can introduce duplicates. Clearing `authors/` and `publisher/` before a clean rebuild avoids this.
- **BibLaTeX parsing errors** — malformed or unsupported LaTeX macros will cause `pybtex` to fail. Validate the source `.bib` file or pre-expand custom macros.
- **Special characters** — `latexcodec` covers most accent and math commands, but you can extend `latex_to_unicode` if a field remains unconverted.

Re-run with `--update-frontmatter-only` while debugging to avoid losing note body edits, and inspect Obsidian previews to confirm wiki-links resolve.

---

## Contributing

Issues and pull requests are welcome. Please open a GitHub issue if you spot a bug, have a question about the workflow, or want to propose an enhancement.
[https://github.com/sjelms/bibtex-to-markdown](https://github.com/sjelms/bibtex-to-markdown)
