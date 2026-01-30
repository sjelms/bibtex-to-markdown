import os
import sys
from typing import Dict, List, Tuple

from pybtex.database import parse_file
from pyzotero import zotero

BIB_FILE = os.environ.get("BIB_FILE", "main.bib")
LIB_ID = os.environ.get("ZOTERO_LIBRARY_ID")
API_KEY = os.environ.get("ZOTERO_API_KEY")
LIB_TYPE = os.environ.get("ZOTERO_LIBRARY_TYPE", "user")
COLLECTION_KEY = os.environ.get("ZOTERO_COLLECTION_KEY")

ITEM_TYPE_MAP = {
    "article": "journalArticle",
    "book": "book",
    "mvbook": "book",
    "booklet": "book",
    "inbook": "bookSection",
    "incollection": "bookSection",
    "chapter": "bookSection",
    "inproceedings": "conferencePaper",
    "proceedings": "conferencePaper",
    "conference": "conferencePaper",
    "thesis": "thesis",
    "phdthesis": "thesis",
    "mastersthesis": "thesis",
    "report": "report",
    "techreport": "report",
    "online": "webPage",
    "www": "webPage",
    "webpage": "webPage",
    "dataset": "dataset",
    "video": "videoRecording",
    "audio": "audioRecording",
    "image": "artwork",
    "periodical": "magazineArticle",
    "legislation": "statute",
    "misc": "document",
    "unpublished": "manuscript",
}


def require_env(value: str, name: str) -> str:
    if not value:
        print(f"Missing required environment variable: {name}")
        sys.exit(1)
    return value


def get_field(entry, *keys: str) -> str:
    for key in keys:
        value = entry.fields.get(key, "").strip()
        if value:
            return value
    return ""


def set_field(template: Dict[str, str], key: str, value: str) -> None:
    if value and key in template:
        template[key] = value


def set_any_field(template: Dict[str, str], keys: Tuple[str, ...], value: str) -> None:
    if not value:
        return
    for key in keys:
        if key in template:
            template[key] = value
            return


def person_to_creator(person, creator_type: str) -> Dict[str, str]:
    first = " ".join(person.first_names + person.middle_names).strip()
    last = " ".join(person.prelast_names + person.last_names + person.lineage_names).strip()
    if not last:
        last = str(person).strip()
    if not first and "," in last:
        parts = [p.strip() for p in last.split(",", 1)]
        if len(parts) == 2:
            last, first = parts[0], parts[1]
    return {"creatorType": creator_type, "firstName": first, "lastName": last}


def get_allowed_creator_types(zot, item_type: str) -> set:
    if item_type in CREATOR_TYPE_CACHE:
        return CREATOR_TYPE_CACHE[item_type]

    allowed: set = set()
    try:
        creator_types = zot.item_creator_types(item_type)
    except Exception:
        creator_types = None

    if isinstance(creator_types, list):
        for entry in creator_types:
            if isinstance(entry, dict):
                creator_type = entry.get("creatorType")
            else:
                creator_type = entry
            if creator_type:
                allowed.add(creator_type)

    if not allowed:
        allowed = {"author", "editor"}

    CREATOR_TYPE_CACHE[item_type] = allowed
    return allowed


def build_creators(entry, allowed_creator_types: set) -> List[Dict[str, str]]:
    creators: List[Dict[str, str]] = []
    for role, creator_type in (("author", "author"), ("editor", "editor")):
        if creator_type not in allowed_creator_types:
            continue
        for person in entry.persons.get(role, []):
            creators.append(person_to_creator(person, creator_type))
    return creators


def map_entry(entry, citekey: str, zot) -> Dict[str, str]:
    bib_type = entry.type.lower()
    item_type = ITEM_TYPE_MAP.get(bib_type, "journalArticle")

    if item_type not in TEMPLATE_CACHE:
        try:
            TEMPLATE_CACHE[item_type] = zot.item_template(item_type)
        except Exception:
            TEMPLATE_CACHE[item_type] = zot.item_template("document")
            item_type = "document"

    template = dict(TEMPLATE_CACHE[item_type])

    title = get_field(entry, "title")
    set_field(template, "title", title or "No Title")
    set_field(template, "DOI", get_field(entry, "doi"))
    set_field(template, "url", get_field(entry, "url"))
    set_field(template, "date", get_field(entry, "date", "year"))
    set_field(template, "abstractNote", get_field(entry, "abstract"))

    set_any_field(template, ("publicationTitle",), get_field(entry, "journaltitle", "journal"))
    set_any_field(template, ("bookTitle", "proceedingsTitle"), get_field(entry, "booktitle"))
    set_field(template, "publisher", get_field(entry, "publisher"))
    set_any_field(template, ("institution", "university"), get_field(entry, "institution", "school"))

    set_field(template, "volume", get_field(entry, "volume"))
    set_field(template, "issue", get_field(entry, "number"))
    set_field(template, "pages", get_field(entry, "pages"))
    set_field(template, "edition", get_field(entry, "edition"))
    set_field(template, "series", get_field(entry, "series"))
    set_any_field(template, ("place",), get_field(entry, "location", "address"))
    set_field(template, "ISBN", get_field(entry, "isbn"))
    set_field(template, "ISSN", get_field(entry, "issn"))
    set_field(template, "language", get_field(entry, "language"))

    if bib_type == "phdthesis":
        set_field(template, "type", "PhD thesis")
    elif bib_type == "mastersthesis":
        set_field(template, "type", "Master's thesis")

    allowed_creator_types = get_allowed_creator_types(zot, item_type)
    creators = build_creators(entry, allowed_creator_types)
    if creators and "creators" in template:
        template["creators"] = creators

    if COLLECTION_KEY:
        template["collections"] = [COLLECTION_KEY]

    return template


def summarize_response(response: Dict[str, Dict[str, Dict[str, str]]]) -> Tuple[int, int, int]:
    successful = response.get("successful", {})
    failed = response.get("failed", {})
    unchanged = response.get("unchanged", {})
    return len(successful), len(failed), len(unchanged)


def log_failures(response: Dict[str, Dict[str, Dict[str, str]]], limit: int = 3) -> None:
    failed = response.get("failed", {})
    if not failed:
        return
    print("  Failed item details:")
    for i, (key, info) in enumerate(failed.items()):
        if i >= limit:
            break
        message = info.get("message", "Unknown error")
        print(f"   - {key}: {message}")


def main() -> None:
    require_env(LIB_ID, "ZOTERO_LIBRARY_ID")
    require_env(API_KEY, "ZOTERO_API_KEY")

    if not os.path.exists(BIB_FILE):
        print(f"Error: {BIB_FILE} not found.")
        sys.exit(1)

    print("--- Starting Zotero Sync ---")

    try:
        zot = zotero.Zotero(LIB_ID, LIB_TYPE, API_KEY)
        print(f"Connected to Zotero library: {LIB_ID} ({LIB_TYPE})")
    except Exception as exc:
        print(f"Connection failed: {exc}")
        sys.exit(1)

    try:
        bib_data = parse_file(BIB_FILE)
    except Exception as exc:
        print(f"Failed to parse {BIB_FILE}: {exc}")
        sys.exit(1)

    entries = list(bib_data.entries.items())
    print(f"Loaded {len(entries)} entries from {BIB_FILE}.")

    print("Fetching existing Zotero library for duplicates...")
    existing_items = zot.everything(zot.top(fields=["data"]))
    existing_dois = set()
    existing_titles = set()
    for item in existing_items:
        data = item.get("data", {})
        doi = (data.get("DOI") or "").lower()
        title = (data.get("title") or "").lower().strip()
        if doi:
            existing_dois.add(doi)
        if title:
            existing_titles.add(title)

    to_add = []
    skipped = 0
    for citekey, entry in entries:
        doi = get_field(entry, "doi").lower()
        title = get_field(entry, "title").lower().strip()
        if (doi and doi in existing_dois) or (title and title in existing_titles):
            skipped += 1
            continue
        try:
            to_add.append(map_entry(entry, citekey, zot))
        except Exception as exc:
            print(f"Skipping {citekey} due to mapping error: {exc}")

    if not to_add:
        print(f"Library is up to date. Skipped {skipped} duplicates.")
        return

    print(f"Pushing {len(to_add)} new items to Zotero...")
    batch_size = 50
    total_success = 0
    total_failed = 0
    total_unchanged = 0

    for i in range(0, len(to_add), batch_size):
        batch = to_add[i : i + batch_size]
        print(f"  Sending batch {i // batch_size + 1} ({len(batch)} items)...")
        response = zot.create_items(batch)
        success, failed, unchanged = summarize_response(response)
        total_success += success
        total_failed += failed
        total_unchanged += unchanged
        print(f"  Batch result: {success} success, {failed} failed, {unchanged} unchanged.")
        if failed:
            log_failures(response)

    print(
        f"--- Sync Complete: {total_success} success, {total_failed} failed, "
        f"{total_unchanged} unchanged. ---"
    )

    if total_failed:
        sys.exit(1)


TEMPLATE_CACHE: Dict[str, Dict[str, str]] = {}
CREATOR_TYPE_CACHE: Dict[str, set] = {}


if __name__ == "__main__":
    main()
