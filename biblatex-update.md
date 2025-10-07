# 🧭 Migrate BibTeX → BibLaTeX using **pybtex** (CI-safe)

This document describes how to migrate your GitHub-Actions pipeline and `convert_bibtex.py` script from classic **BibTeX** (via `bibtexparser`) to **BibLaTeX** (via `pybtex`).  
It preserves your workflow (reference manager → Git push → CI generates Markdown → Obsidian sync) while adding modern fields (ISO dates, editors, org authors, media types) and better Unicode handling.

---

## 0. Goals & outcomes

- Parse **BibLaTeX** `.bib` files natively (still accepts BibTeX).
- Use **structured people parsing** (authors, editors, institutions).
- Prefer **ISO date** (`date = {YYYY-MM-DD}`) but gracefully fall back to `year`/`month`.
- Keep **Markdown/YAML output** structure unchanged unless noted.
- **CI-only change**: install `pybtex` in GitHub Actions (no local install required).

---

## 1. Update GitHub Actions workflow (CI)

Edit `.github/workflows/<your-workflow>.yml` so the runner installs `pybtex` and runs your converter.

```yaml
name: Build notes from .bib

on:
  push:
    paths:
      - 'main.bib'
      - 'convert_bibtex.py'
      - '.github/workflows/**'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install pybtex

      - name: Run converter
        run: python convert_bibtex.py

      - name: Commit generated notes (if changed)
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add .
          git diff --quiet && echo "No changes" || (git commit -m "chore: regenerate notes from .bib" && git push)
```

> During migration you may also install both parsers for safety: `pip install pybtex bibtexparser`.

---

## 2. Minimal refactor of `convert_bibtex.py`

### 2.1 Replace imports

```python
# OLD
# import bibtexparser

# NEW
from pybtex.database import parse_file
from pybtex.textutils import latex_to_unicode
```

### 2.2 Replace BibTeX loading logic

```python
# OLD
# with open(BIBTEX_FILE, "r", encoding="utf-8") as bibfile:
#     bib_database = bibtexparser.load(bibfile)

# NEW
bib_data = parse_file(BIBTEX_FILE)   # supports BibTeX & BibLaTeX
```

### 2.3 Helpers for safe field access & ISO date

Add these helpers near the top of your script:

```python
def get_field(fields, *names, default=""):
    """Return the first present field among names."""
    for n in names:
        v = fields.get(n)
        if v:
            return v
    return default

def get_iso_date(fields):
    """
    Prefer BibLaTeX 'date' (YYYY or YYYY-MM or YYYY-MM-DD).
    Fallback to BibTeX 'year' + 'month' + optional 'day'.
    Returns 'YYYY', 'YYYY-MM', or 'YYYY-MM-DD' (string) or ''.
    """
    d = fields.get("date")
    if d:
        return d

    year = fields.get("year")
    month = fields.get("month")
    day = fields.get("day")

    if not year:
        return ""

    month_map = {
        "jan":"01","feb":"02","mar":"03","apr":"04","may":"05","jun":"06",
        "jul":"07","aug":"08","sep":"09","oct":"10","nov":"11","dec":"12"
    }
    if month:
        m = month.strip().lower()
        m = month_map.get(m, m.zfill(2) if m.isdigit() else "")
    else:
        m = ""

    d_str = str(day).zfill(2) if day and str(day).isdigit() else ""
    if year and m and d_str:
        return f"{year}-{m}-{d_str}"
    if year and m:
        return f"{year}-{m}"
    return str(year)
```

### 2.4 People formatting via pybtex (replace manual author parsing)

```python
def format_persons(persons):
    """
    Return list of Obsidian wikilinks for persons, preserving institutions.
    Output: ['[[First Last]]', '[[US Department of ...]]', ...]
    """
    out = []
    for p in persons:
        # Individuals have last_names and (typically) first_names
        if p.last_names and p.first_names:
            first = " ".join(p.first_names)
            last  = " ".join(p.last_names)
            out.append(f"[[{first} {last}]]")
        else:
            # Institutions: stored in last_names (due to braces in .bib)
            org_parts = p.prelast_names + p.last_names + p.lineage_names
            org = " ".join(org_parts).strip()
            out.append(f"[[{org}]]")
    return out
```

### 2.5 Update the main loop header & field access

Replace your `for entry in bib_database.entries:` block with:

```python
for key, entry in bib_data.entries.items():
    fields = entry.fields
    entry_type = entry.type  # 'article', 'book', 'techreport', 'online', 'video', 'audio', 'dataset', ...

    # Text fields (LaTeX → Unicode for display)
    raw_title = get_field(fields, "title", default="Untitled")
    title = latex_to_unicode(raw_title)

    # Dates
    iso_date = get_iso_date(fields)
    year = fields.get("year", iso_date[:4] if iso_date else "Unknown Year")

    # People
    authors = format_persons(entry.persons.get("author", [])) or ["[[Unknown Author]]"]
    editors = format_persons(entry.persons.get("editor", []))

    # Entities
    publisher   = latex_to_unicode(get_field(fields, "publisher"))
    institution = latex_to_unicode(get_field(fields, "institution", "organization"))
    journal     = latex_to_unicode(get_field(fields, "journaltitle", "journal"))
    url         = get_field(fields, "url")
    doi         = get_field(fields, "doi")
    isbn        = get_field(fields, "isbn")

    # ...the rest of your YAML/Markdown generation stays the same...
```

### 2.6 Add ISO date to YAML (keep year for compatibility)

Where you build `yaml_lines`:

```python
if iso_date:
    yaml_lines.append(f"date: {iso_date}")
else:
    yaml_lines.append(f"year: {year}")
```

(Optional: keep both if other tools still expect `year`.)

---

## 3. Field mapping (what you gain automatically)

| Concept                          | BibTeX (old)                   | BibLaTeX (new)               | Access in code                                           |
|----------------------------------|--------------------------------|------------------------------|----------------------------------------------------------|
| ISO Date                         | `year` + `month` + (day)       | `date`                       | `get_iso_date(fields)`                                   |
| Journal title                    | `journal`                      | `journaltitle`               | `get_field(fields,"journaltitle","journal")`             |
| Institution vs. Organization     | `institution`                  | `organization`               | `get_field(fields,"institution","organization")`         |
| Publisher location               | `address`                      | `location`                   | `get_field(fields,"location","address")`                 |
| URL / DOI / ISBN / ISSN          | sometimes ignored              | first-class fields           | `url`, `doi`, `isbn`, `issn`                             |
| Media types                      | `@misc` catch-all              | `@online`, `@video`, `@audio`, `@dataset`, … | `entry.type`                                 |
| Names (people/institutions)      | manual string parsing          | structured persons           | `entry.persons['author'/'editor']`                       |

---

## 4. Keep existing helpers (with small tweaks)

- **`clean_text()`**: keep it for YAML safety, but apply **after** `latex_to_unicode()` when you’re going to display text (title, publisher, abstract).
- **`normalize_entity_name()`**: keep; great for Obsidian page names.
- **`format_chicago_bibliography()`**: keep; pass it Unicode-converted text to ensure diacritics render correctly.

Example call:

```python
bibliography = format_chicago_bibliography(
    authors,
    year,
    latex_to_unicode(title),
    (publisher or journal or institution),
    url or (f"https://doi.org/{doi}" if doi else "")
)
```

---

## 5. Optional enhancements

- Add `type:` to YAML for downstream processing:
  ```python
  yaml_lines.append(f"type: {entry_type}")
  ```
- Map certain entry types to human labels in your body text:
  - `online` → `[Blog Post]` or `[Web Page]`
  - `video`  → `[Video]`
  - `audio`  → `[Podcast]`
  - `dataset`→ `[Dataset]`

---

## 6. Testing checklist (CI + output)

1. Create a **test branch**: `git checkout -b pybtex-migration`.
2. Commit the workflow and script changes; push; confirm the Action runs.
3. Inspect generated Markdown:
   - Authors & editors render as `[[First Last]]`; institutions preserved.
   - `date:` appears as `YYYY-MM-DD` when available; otherwise `year:`.
   - Unicode characters (e.g., “Bühler”) render correctly.
   - New media types (`@online`, `@video`, `@audio`, `@dataset`) don’t break generation.
4. Diff a sample of files to ensure no unintended frontmatter drift.
5. Merge to `main` when satisfied.

---

## 7. Rollback & dual-compat safety

- Keep a fallback branch using `bibtexparser`.
- During transition, you can keep **both** `date:` and `year:` in YAML to avoid downstream breakage.
- CI can install both parsers temporarily:
  ```bash
  pip install pybtex bibtexparser
  ```

---

## 8) Before/after micro-diff (illustrative)

**Before**

```python
import bibtexparser
with open(BIBTEX_FILE, "r", encoding="utf-8") as bibfile:
    bib_database = bibtexparser.load(bibfile)

for entry in bib_database.entries:
    key = entry.get("ID", "unknown_key")
    year = entry.get("year", "Unknown Year")
    raw_authors = entry.get("author", entry.get("editor", "Unknown Author"))
    # ... manual name parsing & month handling ...
```

**After**

```python
from pybtex.database import parse_file
from pybtex.textutils import latex_to_unicode

bib_data = parse_file(BIBTEX_FILE)

for key, entry in bib_data.entries.items():
    fields = entry.fields
    entry_type = entry.type
    iso_date = get_iso_date(fields)
    year = fields.get("year", iso_date[:4] if iso_date else "Unknown Year")
    authors = format_persons(entry.persons.get("author", [])) or ["[[Unknown Author]]"]
    editors = format_persons(entry.persons.get("editor", []))
    title = latex_to_unicode(fields.get("title", "Untitled"))
    # ... existing YAML/Markdown generation continues ...
```

---

## 9) Notes on editors & your citation style

- Keep editors in YAML as individual links; in your rendered bibliography line you can show:
  `Pedro Rodrigues de Almeida and Michael Bühler (Eds.)`
- This preserves both **graph structure** (Obsidian links) and **clean citation display**.

---

## 10) Summary

- Swap parser: **`bibtexparser` → `pybtex`**.
- Add a tiny ISO-date helper and structured people formatter.
- Keep output structure; gain modern fields & Unicode.
- CI change is a single line (`pip install pybtex`).

After migration, your pipeline remains fully automated: add in the reference manager → Git push updates `.bib` → Action generates Markdown → Obsidian syncs.

---