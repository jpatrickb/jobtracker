"""Listing-file and inbox I/O for the job tracker (see cli.py)."""
import hashlib
import re
from pathlib import Path

from . import store

# DATA_ROOT/LISTINGS_DIR/INBOX_DIR are resolved lazily (store.data_root() etc, called inside the
# functions below) rather than imported as plain names, so merely importing this module never
# triggers a filesystem probe for a data root -- see store.py's module docstring.


def check_duplicate_listing_bodies(records):
    """Find distinct jobs whose saved listing text is byte-identical.

    Two different postings never produce the same text, so a shared body means one capture wrote its
    text over several ids. Anything derived from such a listing (the score, and any fact extracted
    from the text) is worthless until it's re-captured. A cluster counts as triaged once every member
    but one carries a listing_corruption_note, since at most one of them can legitimately own the
    text. Triaged clusters drop to advisories: leaving them as permanent failures would just train
    everyone to ignore doctor, which is how the next untriaged one gets missed."""
    by_body = {}
    for r in records:
        listing = r.get("listing_file")
        if not listing:
            continue
        path = store.data_root() / listing
        if not path.exists():
            continue
        body = read_listing_body(r["id"]) or ""
        body = body.strip()
        if not body:
            continue
        by_body.setdefault(hashlib.md5(body.encode()).hexdigest(), []).append(r)

    problems, advisories = [], []
    for group in by_body.values():
        if len(group) < 2:
            continue
        ids = sorted(r["id"] for r in group)
        annotated = sum(1 for r in group if (r.get("facts") or {}).get("listing_corruption_note"))
        message = (
            f"{len(group)} records share one identical listing body, so at most one can be the real "
            f"posting: {', '.join(ids)}."
        )
        if annotated >= len(group) - 1:
            advisories.append(message + " Triaged: the non-owners carry a listing_corruption_note.")
        else:
            problems.append(
                message + " Re-capture the others; their scores and any facts read from the text are "
                "void. Record a listing_corruption_note on each non-owner to acknowledge it."
            )
    return problems, advisories


def pending_inbox_files():
    inbox_dir = store.inbox_dir()
    if not inbox_dir.exists():
        return []
    return sorted(f for f in inbox_dir.glob("*.md") if f.name != "README.md")


def split_frontmatter(text):
    """Split a leading `---`-delimited frontmatter block off `text`.

    Returns (facts_dict_or_None, body). facts_dict is None when there is no parseable frontmatter
    block, in which case body is the original text unchanged. Shared by inbox files (which may carry
    a `url:` frontmatter block from whatever captured them) and listings/<id>.md (which `write_listing`
    below writes with a fuller company/role/source/url/facts block)."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    data = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        data[k.strip()] = v.strip()
    return data, text[end + 5:].lstrip("\n")


def guess_inbox_title(text):
    _, body = split_frontmatter(text)
    for line in body.splitlines():
        line = line.strip()
        if line and not line.startswith("http"):
            return line
    return "(no title found)"


def extract_linkedin_job_id(text):
    m = re.search(r"currentJobId=(\d+)", text)
    return m.group(1) if m else None


def read_listing_body(id_):
    """Return the text below the frontmatter of an existing listings/<id>.md, or None."""
    dest = store.listings_dir() / f"{id_}.md"
    if not dest.exists():
        return None
    _, body = split_frontmatter(dest.read_text())
    return body


def parse_listing_frontmatter(path):
    """Return the key: value frontmatter of listings/<id>.md as a dict of strings, or None if
    the file has no parseable frontmatter block."""
    data, _ = split_frontmatter(path.read_text())
    return data


def write_listing(id_, company, role, source, url, facts, date_scored, text_path=None):
    """Write listings/<id>.md: a frontmatter header (company/role/source/url/facts/date_scored)
    over the raw posting body. If text_path is given, that becomes the body; otherwise the
    existing body for this id is preserved (used when a field changes after the fact, e.g.
    set-source). Returns the relative path.

    If text_path's own content starts with a frontmatter block (e.g. an inbox file forwarded
    as-is), that block is stripped rather than nested inside the body: its `url:` line is
    bookkeeping to get the URL into *this* function's own `url` argument, not posting content,
    so it shouldn't end up duplicated inside the saved listing text."""
    listings_dir = store.listings_dir()
    listings_dir.mkdir(exist_ok=True)
    if text_path:
        _, body = split_frontmatter(Path(text_path).read_text())
        body = body.strip()
    else:
        body = (read_listing_body(id_) or "").strip()
    lines = ["---", f"company: {company}", f"role: {role}", f"source: {source or ''}", f"url: {url or ''}"]
    for key, value in (facts or {}).items():
        lines.append(f"{key}: {'' if value is None else value}")
    lines.append(f"date_scored: {date_scored}")
    lines.append("---\n")
    header = "\n".join(lines) + "\n"
    dest = listings_dir / f"{id_}.md"
    dest.write_text(header + body + "\n")
    return f"listings/{id_}.md"
