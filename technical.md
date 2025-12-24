# TECHNICAL DOCUMENTATION

## 📌 Project Overview

- **Project Name**: BibLaTeX to Markdown Converter
- **Description**: Python tooling that converts BibLaTeX (and legacy BibTeX) entries into Markdown notes with YAML frontmatter, tailored for Obsidian’s wiki-linking and academic citation workflows. The pipeline ingests a `.bib` database, produces per-citation Markdown with rich metadata, and maintains author/editor and publisher/journal maps of content (MOCs).
- **Primary Technology Stack**: 
  - Python 3.13
  - `pybtex` for BibLaTeX/BibTeX parsing
  - `latexcodec` for robust LaTeX-to-Unicode decoding
  - GitHub Actions (automation)
- **Target Environment**: 
  - Local development: macOS/Linux/Windows with Python 3.9+
  - Automation: GitHub Actions runner (Ubuntu)
- **Prerequisites**: 
  - Python 3.9 or higher
  - Python packages: `pybtex`, `latexcodec`
  - Valid BibLaTeX-formatted input file (`main.bib`)

---

## 🗂️ Directory Structure

```
/bibtex-to-markdown
│
├── convert_bibtex.py     # Main conversion script
├── main.bib             # Input BibLaTeX file
├── titles/             # Output directory for citation files
├── authors/            # Output directory for author and editor files
├── publisher/          # Output directory for publisher and journal files
├── type/               # Output directory for type/decade/year directories
├── technical.md        # Technical documentation
└── README.md          # Project overview and usage instructions
```

- **`convert_bibtex.py`**: Core script handling BibLaTeX parsing, normalization, and markdown generation
- **`main.bib`**: Input BibLaTeX file containing citations to be processed
- **`titles/`**: Generated markdown files for each citation, with YAML frontmatter and formatted content
- **`authors/`**: Generated markdown files for each author/editor, containing cross-references to their publications
- **`publisher/`**: Generated markdown files for each publisher and journal, each listing related citations
- **`type/`**: Generated directories summarizing citations per BibLaTeX entry type, grouped by decade/year
- **`technical.md`**: Detailed technical documentation of the project
- **`README.md`**: Project overview, setup instructions, and basic usage guide

---

## ⚙️ Setup Instructions

### 1. Obtain the Source Code

Clone the repository:
```bash
git clone https://github.com/sjelms/bibtex-to-markdown.git
cd bibtex-to-markdown
```

### 2. Install Dependencies

Install the required Python packages:
```bash
pip install pybtex latexcodec
```

### 3. Configuration

1. Place your BibLaTeX/BibTeX file in the root directory as `main.bib`
2. Ensure the file uses valid BibLaTeX/BibTeX formatting (fields such as `date`, `journaltitle`, `institution`, editors, etc. are supported)
3. Directory Structure:
   - The script creates and updates `titles/` for citation files
   - The script creates `authors/` for author/editor files
   - The script creates `publisher/` for publisher and journal entity files
   - The script creates `type/` for BibLaTeX type directories
   - All directories are created automatically if missing

### 4. Running the Script

Local execution:
```bash
python convert_bibtex.py
```

#### Targeted updates (editors only)
- Use these flags to update only YAML frontmatter for entries that include editors, preserving any custom content in existing files.
  - `--only-with-editors`: process only entries with an `editor` field
  - `--update-frontmatter-only`: replace only the `--- ... ---` YAML block in existing files
  - `--no-author-files`: skip regenerating per-author MOCs during partial updates

Example (recommended for existing notes in `titles/`):
```bash
python convert_bibtex.py --only-with-editors --update-frontmatter-only --no-author-files
```

GitHub Actions:
- The script will run automatically when changes are pushed to the repository
- Generated files will be committed back to the repository

-----

## 🧱 Project Architecture

### 🌀 High-Level Workflow

1. **Input Processing**
   - Parse the `.bib` database with `pybtex`, supporting BibLaTeX fields (`date`, `journaltitle`, `institution`, editors, aliases, etc.)
   - Normalize entry type metadata, authors, and editors from structured `Person` objects
   - Gracefully handle LaTeX-encoded characters via `latexcodec`

2. **Text Processing & Cleaning**
   - Convert LaTeX-escaped sequences to Unicode (`latex_to_unicode`)
   - Clean titles, institutions, and entity names for YAML and display contexts
   - Generate ISO-formatted dates using BibLaTeX `date` or `year`/`month`/`day` fallbacks
   - Normalize keywords into Obsidian-friendly tags

3. **Citation File Generation**
   - Emit markdown files per citation with YAML frontmatter and callouts (`[!bibliography]`, `[!abstract]`)
   - Populate aliases (full and short titles) for Obsidian searchability
   - Link to institutions, journals, and publishers using wiki-links
   - Produce Chicago-style bibliography strings (currently optimized for personal names)

4. **Author/Editor File Generation**
   - Create individual markdown files for each author/editor name encountered
   - Cross-reference all citations and embed bibliography callouts
   - Track institutions the author is associated with (first institution captured in YAML)

5. **Publisher/Journal Page Generation**
   - Create pages for normalized publisher and journal entity names
   - Track and list related citations for each entity, preserving display aliases

### 🧩 Core Components

| Component | Purpose |
| --- | --- |
| `latex_to_unicode()` | Converts LaTeX-encoded fields to Unicode using `latexcodec`, ensuring consistent handling of accented characters and math symbols. |
| `clean_text()` | Normalizes text fields for YAML/non-YAML contexts, removing braces and dangerous characters while preserving content. |
| `format_persons()` | Uses `pybtex` Person objects to create Obsidian `[[Wiki Links]]` for authors and editors, preserving institutions when no personal name is present. |
| `format_chicago_bibliography()` | Produces a Chicago-style bibliography line for each citation (note: institutional names currently follow personal-name formatting). |
| `process_keywords()` | Splits BibLaTeX keyword strings on commas/semicolons, cleans them, and emits lowercase slug-style tags. |
| `normalize_entity_name()` | Cleans publisher/journal names for use as filenames and wiki-links. |
| Main loop | Coordinates parsing, YAML generation, and the creation of title, author, and publisher markdown files. |

-----

## 🧪 Testing & Validation

### Testing Strategy
- Run the converter locally against `main.bib` after significant changes (`python convert_bibtex.py --no-author-files` is a fast smoke test).
- Inspect generated Markdown within Obsidian to verify wiki-links, aliases, and callouts.
- GitHub Actions workflow (`.github/workflows/bibtex-to-md.yml`) executes the script on pushes and surfaces any exceptions in CI logs.

### Sample Data
- Example BibLaTeX entries live in `main.bib` and exercise a wide range of fields (dates, DOIs, institutions, keywords, etc.).
- Generated outputs can be reviewed inside `titles/`, `authors/`, and `publisher/` after a run.

### Known Limitations
- Chicago bibliography formatter currently treats institutional authors as personal names, resulting in awkward “Last, First” formatting for organizations.
- Author and entity aggregation stores citation keys in lists; running the script multiple times without cleanup can introduce duplicate backlinks.
- The generator assumes `pybtex` can parse the `.bib` file; heavily custom BibTeX macros may still require manual preprocessing.
- Crossref’d or inherited fields (e.g., from `@InProceedings`/`@Proceedings`) rely on the merged record provided by `pybtex`; ensure the source file resolves these references.

-----

## ✨ Core Logic & Processing Rules

### Stage 1: BibLaTeX Parsing
- `pybtex.database.parse_file` parses the input and exposes `Entry`/`Person` objects with all BibLaTeX fields intact.
- The converter prioritizes the BibLaTeX-native `date` field but falls back to `year`/`month`/`day` when necessary, normalizing months (e.g., `mar` → `03`).
- Entry types and keys are preserved verbatim and surfaced in the YAML (`type: "[[@article]]"`, `key: "[[@Doe2024-ab]]"`).

### Stage 2: Text Normalization
- `latex_to_unicode` decodes LaTeX sequences using UTF-8 as the source encoding, ensuring consistent handling of accents and special symbols.
- `clean_text` differentiates between YAML and body contexts, stripping braces, converting reserved characters (colons, ampersands), and collapsing whitespace only where required.
- `normalize_entity_name` produces filesystem- and wiki-safe versions of publisher/journal names, while `get_safe_filename` ensures author filenames do not contain forbidden characters.
- `process_keywords` splits on commas/semicolons, removes escape characters, and emits hyphenated tags (e.g., `Workplace Learning` → `Workplace-Learning`).

### Stage 3: Markdown Generation
- **Citation files (`titles/@Key.md`)** include YAML frontmatter with ordered `author - n`/`editor - n` entries, aliases, entity links, tags, and the citation key. The body contains:
  ```markdown
  > [!bibliography]
  > Felstead, Alan, Alison Fuller, Nick Jewson, and Lorna Unwin. 2011. “Praxis: Working to Learn, Learning to Work.” [[UK Commission for Employment and Skills]]. https://doi.org/10.xxxx.

  > [!abstract]
  > …
  ```
  Abstract callouts are added only when an `abstract` field exists.
- **Author files (`authors/Name.md`)** collect all citation backlinks for a given `[[Name]]`, add optional institution metadata, and embed each bibliography using `![[...]]` so changes in the source citation propagate automatically.
- **Publisher/Journal files (`publisher/Entity.md`)** follow the same MOC pattern, grouping related citations under “Content:” with display aliases derived from the citation’s title.
- **Type directories (`type/@entrytype.md`)** provide decade → year rollups for each BibLaTeX entry type with bullet lists sorted by primary author and rendered using the long alias.
- Optional CLI flags (`--only-with-editors`, `--update-frontmatter-only`, `--no-author-files`) allow incremental updates without regenerating the entire knowledge graph.

#### Citation Files:
```markdown
---
title: Paper Title
year: 2023
author - 1: "[[Author Name]]"
editor - 1: "[[Editor Name]]"  # Present only when BibLaTeX has `editor`
key: "[[@Citation-Key]]"
booktitle: Book Title  # Present only when BibLaTeX has `booktitle`
aliases:
  - Full Title Case
  - Short Title Case
publisher: "[[Publisher]]" # Optional, Present only when BibLaTeX has `publisher`
journal: "[[Journal]]" # Optional, Present only when BibLaTeX has `journaltitle`
type: "[[@type]]"
tags:
  - keyword1
  - keyword2
---

> [!bibliography]
> Bibliography formatting

> [!abstract]
> Abstract text
```

>**Note:** The bibliography callout format must be consistent as it will be embedded in author files.

#### Author Files:

```markdown
---
author: "[[Author Name]]"
institution: "[[Institution Name]]"  # Optional, Present only when BibLaTeX has `institution`
field:
type:
aliases:
  - Surname
---

## Author Name
### Content:
[[@Citation-Key|Short Title]]
#### Bibliography:

![[@Citation-Key]]
```


#### Editor Notes
- Editors are treated like authors for note generation to ensure every `[[Name]]` link resolves.
- If a person appears only as an editor, they still get a note under `authors/`.

#### Publisher/Journal Pages
- A page is generated for each unique publisher and journal in `publisher/`.
- Names are normalized by removing punctuation and collapsing spaces (e.g., `John Wiley and Sons, Inc.` → `John Wiley and Sons Inc`).
- The normalized name is used both for the wiki-link `[[...]]` in citation YAML and as the filename.
- If the same normalized name appears as both a publisher and a journal, a single page is created with both categories.

Example YAML for a publisher/journal page:

```markdown
---
name: John Wiley and Sons Inc
aliases:
see also:
tags:
category:
  - publisher
---

## John Wiley and Sons Inc

### Content:
[[@Klein2022-xj|Why Housing Is So Expensive — Particularly In Blue States]]
[[@Klein2023-qs|The Story Construction Tells About America’s Economy Is Disturbing]]
[[@Klein2023-sw|The Dystopia We Fear Is Keeping Us From The Utopia We Deserve]]
[[@Klein2025-yx|Abundance]]
```

#### Interdependency:
- Author files use `![[@Citation-Key]]` to embed the bibliography section from citation files
- The `!` in the syntax causes Obsidian to display the actual bibliography content
- Consistent formatting in citation files is crucial as their content is rendered in multiple places
- This creates automatic updates: changes to a citation's bibliography are reflected everywhere it's embedded

### Data Flow Summary
1. Load entries from `main.bib`.
2. For each entry, generate citation markdown, update author/editor aggregates, track publisher/journal entities, and queue records for type directories.
3. After processing all entries, emit author, entity, and type MOCs unless suppressed via CLI flags.
4. Print a run summary indicating how many entries were processed and which directories were touched.

-----

## 🛠️ Automation & Deployment

### GitHub Actions Integration
- Automated execution on repository changes
- Workflow steps:
  1. Check out repository
  2. Set up Python environment
  3. Install dependencies
  4. Run conversion script
  5. Commit and push generated files

### Local Development
- Script can be run manually for testing
- No additional deployment needed
- Files are generated in local directories

-----

## 🧾 Logs and Debugging

### Common Issues
1. **BibLaTeX Parsing Errors**
   - Validate the source `.bib` file with a BibLaTeX-aware tool; unmatched braces or malformed macros will cause `pybtex` to abort.
   - Confirm LaTeX commands used in fields are supported by `latexcodec` or pre-expand them.

2. **Name/Institution Handling**
   - Institutional authors without personal name parts rely on the `organization` field or braces around the full name; verify those constructs in the source entry.
   - Duplicate backlinks can occur when a script run is repeated; clear the `authors/` and `publisher/` directories if a fresh rebuild is desired.

3. **Markdown Generation Issues**
   - Ensure the repository allows writing to `titles/`, `authors/`, and `publisher/`.
   - Use an Obsidian YAML linter or `yamllint` to confirm frontmatter validity if a run fails midway.

### Troubleshooting
- Re-run the converter with `--update-frontmatter-only` to refresh metadata without overwriting note bodies during debugging.
- Inspect the console summary for the processed entry count; a sudden drop usually signals an upstream parsing failure.
- Validate generated markdown in Obsidian or a Markdown preview to confirm wiki-links resolve as expected.

-----

## 📦 Future Enhancements

- [ ] Improve Chicago bibliography formatting for institutional authors (avoid forced “Last, First” ordering).
- [ ] De-duplicate author/publisher citation lists when regenerating files multiple times in a row.
- [ ] Expand test coverage with sample fixtures and golden-file comparisons in CI.
- [ ] Externalize configuration (input filename, output directories, callout templates) to a `.toml` or `.yaml` file.
- [ ] Optional CSL-based formatter to support additional citation styles beyond Chicago.

---

## 🧾 Alias Support Summary

- Citation notes include an `aliases:` list containing a title-case full title and (when available) a short title truncated at the first colon or dash.
- Author notes append the primary surname to their `aliases:` list, making `[[Surname]]` lookups possible inside Obsidian.
- MOC sections in author and publisher pages use `[[@CitationKey|Display Title]]` link aliases alongside the embedded bibliography (`![[@CitationKey]]`) so readers see both a skim-friendly list and full references.

-----

## 📚 References

- [`pybtex` Documentation](https://pybtex.org/)
- [`latexcodec` Project](https://pypi.org/project/latexcodec/)
- [Obsidian Markdown Format](https://help.obsidian.md/Editing+and+formatting/Basic+formatting+syntax)
- [BibLaTeX Format Guide](https://ctan.org/pkg/biblatex)
- [Chicago Citation Style](https://www.chicagomanualofstyle.org/tools_citationguide.html)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

-----

## 🧑‍💻 Author & Contact

- **Repository**: [bibtex-to-markdown](https://github.com/sjelms/bibtex-to-markdown)
- **Issues**: Please report issues through the GitHub repository
- **Maintainer**: sjelms

<!-- end list -->
