# TECHNICAL DOCUMENTATION

## 📌 Project Overview

- **Project Name**: BibTeX to Markdown Converter
- **Description**: A Python utility that converts BibTeX entries into Markdown notes with YAML frontmatter, optimized for Obsidian's wiki-linking and academic citation workflows. It processes BibTeX files to create individual markdown files for both citations and authors, maintaining bidirectional links between them.
- **Primary Technology Stack**: 
  - Python 3.7+
  - bibtexparser library
  - GitHub Actions (for automation)
- **Target Environment**: 
  - Local development: Any OS with Python 3.7+
  - Automation: GitHub Actions
- **Prerequisites**: 
  - Python 3.7 or higher
  - bibtexparser library
  - Valid BibTeX file input

---

## 🗂️ Directory Structure

```
/bibtex-to-markdown
│
├── convert_bibtex.py     # Main conversion script
├── main.bib             # Input BibTeX file
├── markdown_entries/    # Output directory for citation files
├── authors/            # Output directory for author files
├── technical.md        # Technical documentation
└── README.md          # Project overview and usage instructions
```

- **`convert_bibtex.py`**: Core script handling BibTeX parsing and markdown generation
- **`main.bib`**: Input BibTeX file containing citations to be processed
- **`markdown_entries/`**: Generated markdown files for each citation, with YAML frontmatter and formatted content
- **`authors/`**: Generated markdown files for each author, containing cross-references to their publications
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

Install the required Python package:
```bash
pip install bibtexparser
```

### 3. Configuration

1. Place your BibTeX file in the root directory as `main.bib`
2. Ensure the file uses valid BibTeX formatting
3. Directory Structure:
   - The script will create `markdown_entries/` directory for citation files
   - The script will create `authors/` directory for author files
   - Both directories will be created automatically if they don't exist

### 4. Running the Script

Local execution:
```bash
python convert_bibtex.py
```

GitHub Actions:
- The script will run automatically when changes are pushed to the repository
- Generated files will be committed back to the repository

-----

## 🧱 Project Architecture

### 🌀 High-Level Workflow

1. **Input Processing**
   - Read BibTeX file using bibtexparser
   - Parse entries into Python dictionary format
   - Handle multi-line entries and special characters

2. **Text Processing & Cleaning**
   - Clean and standardize text fields
   - Process author names and institutions
   - Handle escaped characters and special sequences
   - Convert BibTeX-specific formatting

3. **Citation File Generation**
   - Create markdown files for each citation
   - Generate YAML frontmatter with metadata
   - Format bibliography in Chicago style
   - Include abstracts when available
   - Create Obsidian-compatible wiki-links

4. **Author File Generation**
   - Create individual markdown files for each author
   - Cross-reference all citations by the author
   - Maintain bidirectional links with citation files

### 🧩 Core Components

| Component | Purpose |
| --- | --- |
| `clean_text()` | Processes text fields, handling escaped characters, special sequences, and formatting. Supports both YAML and non-YAML contexts. |
| `format_authors()` | Parses and formats author names, handling institutions, name order, and multi-line entries. Creates Obsidian-compatible author links. |
| `format_chicago_bibliography()` | Formats citation data in Chicago style, handling author names, titles, and URLs appropriately. |
| `process_keywords()` | Converts BibTeX keywords into Obsidian-compatible tags, cleaning special characters and formatting. |
| `Main Script` | Orchestrates the overall process, handling file I/O, directory creation, and markdown generation. |

-----

## 🧪 Testing & Validation

### Testing Strategy
- Manual testing with sample BibTeX entries
- Validation of output markdown files in Obsidian
- GitHub Actions integration testing

### Sample Data
- Example BibTeX entries are included in `main.bib`
- Sample outputs can be found in `markdown_entries/` directory

### Known Limitations
- Author names must be properly formatted in BibTeX
- Special characters in BibTeX need proper escaping
- Multi-line author entries require careful formatting
- Institution names in author fields need proper bracketing

-----

## ✨ Core Logic & Processing Rules

### Stage 1: BibTeX Processing
- File is read using bibtexparser library
- Entries are parsed into dictionary format
- Basic validation of required fields
- Empty fields are handled with default values

### Stage 2: Text Processing
- Special character handling:
  - Escaped characters (`\&`, `\_`) are processed appropriately
  - Formatting is preserved where needed
  - URLs are cleaned of trailing punctuation
- Author name processing:
  - Handles "Last, First" and "First Last" formats
  - Preserves institutional authors in braces
  - Splits multiple authors on " and "
  - Handles multi-line author entries

### Stage 3: Markdown Generation
#### Citation Files:

```
---
title: "Paper Title"
year: "2023"
author - 1: "[[Author Name]]"
key: "[[@Citation-Key]]"
tags:
  - keyword1
  - keyword2
---

> [!Bibliography]
> Bibliography formatting in Chicago style

## Abstract
```

Note: The bibliography callout format must be consistent as it will be embedded in author files.

#### Author Files:

```
---
author: "[[Author Name]]"
field: 
institution:
type:
---

## Author first last
#### Bibliography:
![[@Citation-Key]]  # Embeds the bibliography callout from the citation file
```

#### Interdependency:
- Author files use `![[@Citation-Key]]` to embed the bibliography section from citation files
- The `!` in the syntax causes Obsidian to display the actual bibliography content
- Consistent formatting in citation files is crucial as their content is rendered in multiple places
- This creates automatic updates: changes to a citation's bibliography are reflected everywhere it's embedded

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
1. **BibTeX Parsing Errors**
   - Check BibTeX syntax
   - Ensure proper escaping of special characters
   - Verify author name formatting

2. **Author Name Issues**
   - Ensure consistent use of "Last, First" format
   - Check for proper handling of institutions
   - Verify multi-line author entries

3. **File Generation Issues**
   - Check write permissions for output directories
   - Verify file naming conflicts
   - Ensure valid YAML formatting

### Troubleshooting
- Review BibTeX input file for formatting issues
- Check generated markdown files for proper linking
- Verify Obsidian compatibility of generated files

-----

## 📦 Future Enhancements

- [x] Author name parsing improvements
  - Handle multi-line author entries
  - Better institution handling
  - Consistent name formatting

- [x] Special character handling
  - Proper escaping in YAML
  - URL formatting
  - BibTeX escape sequence handling

- [ ] Author File Generation
  - Create individual author pages
  - Maintain citation cross-references
  - Support additional metadata fields

- [ ] Potential Improvements
  - Support for additional BibTeX fields
  - Custom citation styles
  - Enhanced error reporting
  - Configuration file support

---

## 🧾 Planned Features for YAML & Alias Support

- [ ] **Add `aliases:` field to author YAML**
  - Include the author’s **surname** as an alias (e.g. `aliases: [Williams]`)
  - Enables Obsidian references to author notes using just the last name

- [ ] **Add `aliases:` field to citation YAML**
  - Add the **full title** and an optional **short title** (if detected)
  - Example:
    ```yaml
    aliases:
      - A Better Future - Transforming jobs and skills for young people post-pandemic
      - A Better Future
    ```

- [ ] **Update author files to include a Map of Content (MOC)**
  - In addition to existing `![[@CitationKey]]` transclusions
  - Add Obsidian links with alias syntax:
    ```markdown
    [[@Williams2021-iq|A Better Future]]
    ```
  - This allows the author page to show a human-readable title while linking to the citation note

--- 

This action list defines YAML alias support and enhances author pages with more usable maps of content.

-----

## 📚 References

- [bibtexparser Documentation](https://bibtexparser.readthedocs.io/)
- [Obsidian Markdown Format](https://help.obsidian.md/Editing+and+formatting/Basic+formatting+syntax)
- [BibTeX Format Documentation](http://www.bibtex.org/Format/)
- [Chicago Citation Style](https://www.chicagomanualofstyle.org/tools_citationguide.html)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

-----

## 🧑‍💻 Author & Contact

- **Repository**: [bibtex-to-markdown](https://github.com/sjelms/bibtex-to-markdown)
- **Issues**: Please report issues through the GitHub repository
- **Maintainer**: sjelms

<!-- end list -->
