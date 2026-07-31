"""CLI command implementations for the job tracker (see cli.py)."""
import difflib
import json
import re
import sys
from datetime import date, timedelta

from . import store
from .store import STATUSES, TERMINAL_STATUSES, load, save, slugify, make_id, resolve_id, get_field
from .facts import warn_missing_required_facts, load_facts_arg, parse_fact_filter, fact_matches, all_fact_keys
from .scoring import resolve_scorer_version, score_entry, current_scoring_version, scoring_version_number, score_is_behind
from .listings import write_listing, pending_inbox_files, guess_inbox_title, extract_linkedin_job_id
from . import render


def cmd_add(args):
    records = load()
    base_id = f"{slugify(args.company)}-{slugify(args.role)}"
    active = [r for r in records if r["id"] == base_id and r["status"] not in TERMINAL_STATUSES]
    if active and not args.force:
        r = active[0]
        print(
            f"Already tracked as '{r['id']}' (status: {r['status']}). "
            "Use update-status instead, or pass --force to log a new attempt.",
            file=sys.stderr,
        )
        sys.exit(1)

    id_ = make_id(records, args.company, args.role)
    today = date.today().isoformat()
    version = resolve_scorer_version(args.scorer_version)
    facts = load_facts_arg(args.facts, args.facts_file) or {}
    warn_missing_required_facts(facts)
    listing_file = None
    if args.listing_file or facts:
        listing_file = write_listing(
            id_, args.company, args.role, args.source, args.url, facts, today, text_path=args.listing_file
        )
    record = {
        "id": id_,
        "company": args.company,
        "role": args.role,
        # score/band/scorer_version are the CURRENT scoring; score_history is the full series,
        # mirroring how status mirrors status_history[-1]. doctor asserts the two stay in step.
        "score": args.score,
        "band": args.band,
        "scorer_version": version,
        "score_history": [score_entry(args.score, args.band, version, today, args.notes or "")],
        "url": args.url,
        "source": args.source,
        "listing_file": listing_file,
        "facts": facts,
        "folder": None,
        "status": "Scored",
        "status_history": [{"status": "Scored", "date": today, "note": args.notes or ""}],
        "notes": args.notes or "",
        "created_at": today,
        "updated_at": today,
    }
    records.append(record)
    save(records)
    suffix = f", listing saved to {listing_file}" if listing_file else ""
    print(f"Added '{id_}' (Scored, {args.score}/100 - {args.band}, scored by {version}){suffix}")


def cmd_rescore(args):
    """Append a fresh scoring of an already-tracked job, keeping every prior score intact."""
    records = load()
    r = resolve_id(records, args.id)
    if not r:
        sys.exit(1)
    version = resolve_scorer_version(args.scorer_version)
    when = args.date or date.today().isoformat()
    prev_score, prev_version = r.get("score"), r.get("scorer_version")

    if prev_version == version and not args.force:
        print(
            f"'{r['id']}' was already scored by {version}. Rescoring with the same version "
            "replaces a measurement rather than adding a comparable one; pass --force if that's "
            "deliberate (e.g. correcting a mis-score).",
            file=sys.stderr,
        )
        sys.exit(1)

    r.setdefault("score_history", []).append(
        score_entry(args.score, args.band, version, when, args.note or "")
    )
    r["score"], r["band"], r["scorer_version"] = args.score, args.band, version
    r["updated_at"] = when
    save(records)

    if isinstance(prev_score, (int, float)):
        delta = args.score - prev_score
        movement = f" ({prev_score} -> {args.score}, {delta:+d} vs {prev_version})"
    else:
        movement = ""
    print(f"'{r['id']}' rescored {args.score}/100 - {args.band} by {version}{movement}")


def cmd_update_status(args):
    records = load()
    r = resolve_id(records, args.id)
    if not r:
        sys.exit(1)
    today = args.date or date.today().isoformat()
    r["status"] = args.status
    r["status_history"].append({"status": args.status, "date": today, "note": args.note or ""})
    r["updated_at"] = today
    save(records)
    print(f"'{r['id']}' -> {args.status} ({today})")


def cmd_set_folder(args):
    records = load()
    r = resolve_id(records, args.id)
    if not r:
        sys.exit(1)
    r["folder"] = args.path
    r["updated_at"] = date.today().isoformat()
    save(records)
    print(f"'{r['id']}' folder -> {args.path}")


def cmd_set_listing(args):
    records = load()
    r = resolve_id(records, args.id)
    if not r:
        sys.exit(1)
    listing_file = write_listing(
        r["id"], r["company"], r["role"], r.get("source"), r.get("url"),
        r.get("facts", {}), r.get("created_at", date.today().isoformat()), text_path=args.path,
    )
    r["listing_file"] = listing_file
    r["updated_at"] = date.today().isoformat()
    save(records)
    print(f"'{r['id']}' listing -> {listing_file}")


def cmd_set_source(args):
    records = load()
    r = resolve_id(records, args.id)
    if not r:
        sys.exit(1)
    r["source"] = args.source
    r["updated_at"] = date.today().isoformat()
    if r.get("listing_file"):
        write_listing(
            r["id"], r["company"], r["role"], r["source"], r.get("url"),
            r.get("facts", {}), r.get("created_at", r["updated_at"]),
        )
    save(records)
    print(f"'{r['id']}' source -> {args.source}")


def cmd_set_url(args):
    records = load()
    r = resolve_id(records, args.id)
    if not r:
        sys.exit(1)
    r["url"] = args.url if args.url else None
    r["updated_at"] = date.today().isoformat()
    if r.get("listing_file"):
        write_listing(
            r["id"], r["company"], r["role"], r.get("source"), r["url"],
            r.get("facts", {}), r.get("created_at", r["updated_at"]),
        )
    save(records)
    print(f"'{r['id']}' url -> {r['url']}")


def cmd_set_employer(args):
    """Rename the company and/or role on an existing record.

    Needed because an employer is often not knowable at scoring time: staffing firms and
    relist platforms hide it, and it only surfaces later (a redirect to the real ATS, a
    recruiter call). Re-adding the record would lose its status history, so this edits in
    place. The id deliberately does NOT change: it is the stable key that listings/<id>.md,
    the applications/ folder link, and the status history all hang off.
    """
    records = load()
    r = resolve_id(records, args.id)
    if not r:
        sys.exit(1)
    if not args.company and not args.role:
        print("Provide --company and/or --role", file=sys.stderr)
        sys.exit(1)
    changed = []
    for field, value in (("company", args.company), ("role", args.role)):
        if value:
            changed.append(f"{field}: {r[field]!r} -> {value!r}")
            r[field] = value
    r["updated_at"] = date.today().isoformat()
    if r.get("listing_file"):
        write_listing(
            r["id"], r["company"], r["role"], r.get("source"), r.get("url"),
            r.get("facts", {}), r.get("created_at", r["updated_at"]),
        )
    save(records)
    print(f"'{r['id']}' updated ({'; '.join(changed)}); id unchanged")


def cmd_set_facts(args):
    records = load()
    r = resolve_id(records, args.id)
    if not r:
        sys.exit(1)
    new_facts = load_facts_arg(args.facts, args.facts_file)
    if new_facts is None:
        print("Provide --facts '<json>' or --facts-file <path>", file=sys.stderr)
        sys.exit(1)
    facts = r.get("facts", {})
    facts.update(new_facts)
    warn_missing_required_facts(facts)
    r["facts"] = facts
    r["updated_at"] = date.today().isoformat()
    if r.get("listing_file"):
        write_listing(
            r["id"], r["company"], r["role"], r.get("source"), r.get("url"),
            facts, r.get("created_at", r["updated_at"]),
        )
    save(records)
    print(f"'{r['id']}' facts updated: {json.dumps(new_facts)}")


def cmd_unset_fact(args):
    records = load()
    r = resolve_id(records, args.id)
    if not r:
        sys.exit(1)
    facts = r.get("facts") or {}
    if args.key not in facts:
        print(f"'{r['id']}' has no fact '{args.key}'", file=sys.stderr)
        sys.exit(1)
    del facts[args.key]
    r["facts"] = facts
    r["updated_at"] = date.today().isoformat()
    if r.get("listing_file"):
        write_listing(
            r["id"], r["company"], r["role"], r.get("source"), r.get("url"),
            facts, r.get("created_at", r["updated_at"]),
        )
    save(records)
    print(f"'{r['id']}' fact '{args.key}' removed")


def cmd_remove(args):
    records = load()
    r = resolve_id(records, args.id)
    if not r:
        sys.exit(1)
    if not args.force:
        print(
            f"This permanently deletes '{r['id']}' ({r['company']} - {r['role']}, status {r['status']}) "
            "from applications.json and its listing file, if any. Re-run with --force to confirm.",
            file=sys.stderr,
        )
        sys.exit(1)
    records = [x for x in records if x["id"] != r["id"]]
    save(records)
    removed_listing = None
    if r.get("listing_file"):
        path = store.data_root() / r["listing_file"]
        if path.exists():
            path.unlink()
            removed_listing = r["listing_file"]
    suffix = f", removed {removed_listing}" if removed_listing else ""
    print(f"Removed '{r['id']}'{suffix}")


def print_inbox_hint():
    n = len(pending_inbox_files())
    if n:
        print(f"\n{n} more item(s) waiting to be scored in inbox/ (run: jobtracker inbox)")


def cmd_list(args):
    all_records = load()
    known_facts = all_fact_keys(all_records)
    records = all_records
    if args.status:
        records = [r for r in records if r["status"] == args.status]
    if args.company:
        records = [r for r in records if args.company.lower() in r["company"].lower()]
    if args.scorer_version:
        records = [r for r in records if r.get("scorer_version") == args.scorer_version]
    if args.stale_score:
        current = current_scoring_version()
        if not current:
            print("Can't resolve the current scorer version from SCORING.md.", file=sys.stderr)
            sys.exit(1)
        current_number = scoring_version_number(current)
        records = [r for r in records if score_is_behind(r, current_number)]
    for spec in args.fact:
        key, op, value = parse_fact_filter(spec)
        if key not in known_facts:
            close = difflib.get_close_matches(key, known_facts, n=3)
            hint = f" Did you mean: {', '.join(close)}?" if close else " No record has this fact at all."
            print(f"Warning: '{key}' isn't a known fact key.{hint}", file=sys.stderr)
        records = [r for r in records if fact_matches(r.get("facts", {}).get(key), op, value)]

    if not records:
        if args.json:
            print("[]")
        else:
            print("No matching records.")
            print_inbox_hint()
        return

    if args.sort:
        try:
            records.sort(key=lambda r: (get_field(r, args.sort) is None, get_field(r, args.sort)), reverse=args.desc)
        except TypeError:
            print(f"Can't sort by '{args.sort}': values aren't consistently comparable across records", file=sys.stderr)
            sys.exit(1)
    else:
        records.sort(key=lambda r: (STATUSES.index(r["status"]) if r["status"] in STATUSES else 99, -r.get("score", 0)))

    if args.json:
        print(json.dumps(records, indent=2))
        return

    if args.fields:
        fields = [f.strip() for f in args.fields.split(",")]
        rows = [["" if get_field(r, f) is None else str(get_field(r, f)) for f in fields] for r in records]
        if render.is_pretty(args):
            _render_fields_rich(fields, rows)
        else:
            _render_fields_plain(fields, rows)
        print_inbox_hint()
        return

    shaped = _shape_list_rows(records)
    if render.is_pretty(args):
        _render_list_rich(shaped)
    else:
        _render_list_plain(shaped)
    print_inbox_hint()


def _shape_list_rows(records):
    return [
        {
            "id": r["id"],
            "status": r["status"],
            "score": r["score"],
            "band": r.get("band"),
            "company": r["company"],
            "role": r["role"],
            "source": r.get("source"),
        }
        for r in records
    ]


def _render_list_plain(rows):
    width_id = max(len(row["id"]) for row in rows) + 2
    for row in rows:
        src = f"  [{row['source']}]" if row["source"] else ""
        print(f"{row['id']:<{width_id}} {row['status']:<12} {row['score']:>3}/100  {row['company']} - {row['role']}{src}")


def _render_list_rich(rows):
    from rich.table import Table

    # Fixed widths on the short/bounded columns (status is one of a known 9-value enum, score is
    # always "N/100") plus expand=True + ratio=1 on company/role, which is Rich's mechanism for
    # "fill whatever width remains" - computed directly rather than via the wrap-based shrink pass,
    # which (see rich/table.py's _collapse_widths) only ever shrinks columns that have no fixed
    # width AND no_wrap=False, and would otherwise word-wrap that column across multiple lines
    # instead of giving a single ellipsized line.
    table = Table(box=None, pad_edge=False, expand=True)
    table.add_column("id", style="dim", width=20, overflow="ellipsis", no_wrap=True)
    table.add_column("status", width=12, overflow="ellipsis", no_wrap=True)
    table.add_column("score", width=7, justify="right", no_wrap=True)
    table.add_column("company / role", ratio=1, overflow="ellipsis", no_wrap=True)
    table.add_column("source", style="dim", width=18, overflow="ellipsis", no_wrap=True)
    for row in rows:
        table.add_row(
            render.text(row["id"]),
            render.text(row["status"], style=render.status_style(row["status"])),
            render.text(f"{row['score']}/100", style=render.score_style(row["score"], row["band"])),
            render.text(f"{row['company']} - {row['role']}"),
            render.text(row["source"] or ""),
        )
    render.console().print(table)


def _render_fields_plain(fields, rows):
    widths = [max(len(fields[i]), *(len(row[i]) for row in rows)) + 2 for i in range(len(fields))]
    print("".join(f"{fields[i]:<{widths[i]}}" for i in range(len(fields))))
    for row in rows:
        print("".join(f"{row[i]:<{widths[i]}}" for i in range(len(fields))))


def _render_fields_rich(fields, rows):
    from rich.table import Table

    # Fields are arbitrary/dynamic (any column may be the long one), so every column gets an
    # equal ratio share of the terminal width via expand=True rather than picking one to flex -
    # see _render_list_rich's comment for why an un-ratio'd, un-widthed column would either get
    # crushed to nothing or word-wrap instead of ellipsizing.
    table = Table(box=None, pad_edge=False, expand=True)
    for field in fields:
        table.add_column(field, ratio=1, overflow="ellipsis", no_wrap=True)
    for row in rows:
        table.add_row(*(render.text(cell) for cell in row))
    render.console().print(table)


def cmd_show(args):
    records = load()
    r = resolve_id(records, args.id)
    if not r:
        sys.exit(1)
    if args.json:
        print(json.dumps(r, indent=2))
        return

    shaped = _shape_show(r)
    if render.is_pretty(args):
        _render_show_rich(shaped)
    else:
        _render_show_plain(shaped)


def _shape_show(r):
    return {
        "id": r["id"],
        "company": r["company"],
        "role": r["role"],
        "status": r["status"],
        "score": r["score"],
        "band": r["band"],
        "scorer_version": r.get("scorer_version"),
        "source": r.get("source"),
        "url": r.get("url"),
        "folder": r.get("folder"),
        "listing_file": r.get("listing_file"),
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
        "facts": r.get("facts") or {},
        "score_history": r.get("score_history") or [],
        "status_history": r.get("status_history", []),
        "notes": r.get("notes"),
    }


def _render_show_plain(s):
    print(f"{s['id']}")
    print(f"{s['company']} — {s['role']}")
    scored_by = f"  [scored by {s['scorer_version']}]" if s.get("scorer_version") else ""
    print(f"Status: {s['status']:<14} Score: {s['score']}/100 ({s['band']}){scored_by}")
    print(f"Source: {s.get('source') or '(none)'}")
    if s.get("url"):
        print(f"URL:    {s['url']}")
    print(f"Folder:  {s.get('folder') or '(none)'}")
    print(f"Listing: {s.get('listing_file') or '(none)'}")
    print(f"Created: {s['created_at']}   Updated: {s['updated_at']}")

    facts = s["facts"]
    if facts:
        print("\nFacts:")
        width = max(len(k) for k in facts) + 2
        for k, v in facts.items():
            print(f"  {k:<{width}} {v}")

    history = s["score_history"]
    if len(history) > 1:
        print("\nScore history:")
        for entry in history:
            note = f"  ({entry['note']})" if entry.get("note") else ""
            print(f"  {entry['date']}  {entry['score']:>3}/100  {entry['version']:<5} {entry['band']}{note}")

    print("\nStatus history:")
    for entry in s["status_history"]:
        note = f"  ({entry['note']})" if entry.get("note") else ""
        print(f"  {entry['date']}  {entry['status']}{note}")

    if s.get("notes"):
        print(f"\nNotes: {s['notes']}")


def _render_show_rich(s):
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    console = render.console()

    header = Text()
    header.append(f"{s['company']} — {s['role']}\n", style="bold")
    header.append(f"{s['id']}\n", style="dim")
    header.append("Status: ")
    header.append(f"{s['status']:<14}", style=render.status_style(s["status"]))
    header.append(" Score: ")
    header.append(f"{s['score']}/100 ({s['band']})", style=render.score_style(s["score"], s["band"]))
    if s.get("scorer_version"):
        header.append(f"  [scored by {s['scorer_version']}]", style="dim")
    console.print(Panel(header, expand=False))

    console.print(render.text(f"Source: {s.get('source') or '(none)'}"))
    if s.get("url"):
        console.print(render.text(f"URL:    {s['url']}"))
    console.print(render.text(f"Folder:  {s.get('folder') or '(none)'}"))
    console.print(render.text(f"Listing: {s.get('listing_file') or '(none)'}"))
    console.print(render.text(f"Created: {s['created_at']}   Updated: {s['updated_at']}"))

    facts = s["facts"]
    if facts:
        console.print()
        console.print("Facts:", style="bold")
        table = Table(box=None, show_header=False, pad_edge=False)
        table.add_column("key", style="cyan", no_wrap=True)
        table.add_column("value", overflow="fold")
        for k, v in facts.items():
            table.add_row(render.text(k), render.text(v))
        console.print(table)

    history = s["score_history"]
    if len(history) > 1:
        console.print()
        console.print("Score history:", style="bold")
        table = Table(box=None, show_header=False, pad_edge=False)
        table.add_column("date", no_wrap=True)
        table.add_column("score", justify="right", no_wrap=True)
        table.add_column("version", no_wrap=True)
        table.add_column("band / note", overflow="fold")
        for entry in history:
            note = f"  ({entry['note']})" if entry.get("note") else ""
            table.add_row(
                render.text(entry["date"]),
                render.text(f"{entry['score']}/100", style=render.score_style(entry["score"], entry.get("band"))),
                render.text(entry["version"]),
                render.text(f"{entry['band']}{note}"),
            )
        console.print(table)

    console.print()
    console.print("Status history:", style="bold")
    table = Table(box=None, show_header=False, pad_edge=False)
    table.add_column("date", no_wrap=True)
    table.add_column("status", no_wrap=True)
    table.add_column("note", overflow="fold")
    for entry in s["status_history"]:
        table.add_row(
            render.text(entry["date"]),
            render.text(entry["status"], style=render.status_style(entry["status"])),
            render.text(entry.get("note") or ""),
        )
    console.print(table)

    if s.get("notes"):
        console.print()
        console.print(Text("Notes: ", style="bold") + render.text(s["notes"]))


def cmd_inbox(args):
    files = pending_inbox_files()
    if not files:
        print("Inbox is empty, nothing waiting to be scored.")
        return
    print(f"{len(files)} item(s) waiting to be scored in inbox/:")
    width = max(len(f.name) for f in files) + 2
    for f in files:
        print(f"  {f.name:<{width}} {guess_inbox_title(f.read_text())}")


def cmd_inbox_dupes(args):
    files = pending_inbox_files()
    if not files:
        print("Inbox is empty.")
        return

    entries = [
        {"file": f.name, "text": (text := f.read_text()), "job_id": extract_linkedin_job_id(text),
         "title": guess_inbox_title(text)}
        for f in files
    ]

    already_scored_by_job_id = {}
    for r in load():
        job_id = extract_linkedin_job_id(r.get("url") or "")
        if not job_id and r.get("listing_file"):
            path = store.data_root() / r["listing_file"]
            if path.exists():
                job_id = extract_linkedin_job_id(path.read_text())
        if job_id:
            already_scored_by_job_id.setdefault(job_id, r["id"])

    found = False

    for e in entries:
        if e["job_id"] and e["job_id"] in already_scored_by_job_id:
            found = True
            print(f"Already scored: {e['file']} ({e['title']!r}) matches '{already_scored_by_job_id[e['job_id']]}'")

    by_job_id = {}
    for e in entries:
        if e["job_id"]:
            by_job_id.setdefault(e["job_id"], []).append(e["file"])
    for job_id, group in by_job_id.items():
        if len(group) > 1:
            found = True
            print(f"Duplicate posting (currentJobId={job_id}): {', '.join(group)}")

    flagged = set()
    for i, a in enumerate(entries):
        for b in entries[i + 1:]:
            if a["title"] == "(no title found)" or a["job_id"] and a["job_id"] == b["job_id"]:
                continue
            ratio = difflib.SequenceMatcher(None, a["title"].lower(), b["title"].lower()).ratio()
            if ratio >= args.threshold:
                found = True
                flagged.add(a["file"])
                flagged.add(b["file"])
                print(f"Similar titles ({ratio:.0%}): {a['file']} ({a['title']!r}) vs {b['file']} ({b['title']!r})")

    if not found:
        print(f"No duplicates detected across {len(entries)} inbox item(s).")


def cmd_search(args):
    pattern_text = args.term if args.regex else re.escape(args.term)
    try:
        pattern = re.compile(pattern_text, re.IGNORECASE)
    except re.error as e:
        print(f"Invalid regex: {e}", file=sys.stderr)
        sys.exit(1)

    records = load()
    found = False
    for r in records:
        listing_file = r.get("listing_file")
        if not listing_file:
            continue
        path = store.data_root() / listing_file
        if not path.exists():
            continue
        text = path.read_text()
        m = pattern.search(text)
        if not m:
            continue
        found = True
        snippet = " ".join(text[max(0, m.start() - 40):m.end() + 40].split())
        print(f"{r['id']}: …{snippet}…")

    if not found:
        print("No matches.")


def resolve_date_arg(value):
    if value in ("today", None):
        return date.today().isoformat()
    if value == "yesterday":
        return (date.today() - timedelta(days=1)).isoformat()
    try:
        date.fromisoformat(value)
    except ValueError:
        print(f"Invalid date '{value}'; expected YYYY-MM-DD, 'today', or 'yesterday'.", file=sys.stderr)
        sys.exit(1)
    return value


def cmd_activity(args):
    records = load()
    target = resolve_date_arg(args.date)
    hits = []
    for r in records:
        events = [
            h for h in r.get("status_history", [])
            if h.get("date") == target and (not args.status or h.get("status") == args.status)
        ]
        if events:
            hits.append((r, events))

    if args.json:
        print(json.dumps(
            [{"id": r["id"], "company": r["company"], "role": r["role"], "events": events} for r, events in hits],
            indent=2,
        ))
        return

    if not hits:
        label = "with a status change" if not args.status else f"that moved to '{args.status}'"
        print(f"No records {label} on {target}.")
        return

    shaped = _shape_activity(hits)
    if render.is_pretty(args):
        _render_activity_rich(shaped)
    else:
        _render_activity_plain(shaped)


def _shape_activity(hits):
    return [
        {
            "id": r["id"],
            "company": r["company"],
            "role": r["role"],
            "statuses": [e["status"] for e in events],
            "events": events,
        }
        for r, events in hits
    ]


def _render_activity_plain(rows):
    width_id = max(len(row["id"]) for row in rows) + 2
    for row in rows:
        statuses = ", ".join(row["statuses"])
        print(f"{row['id']:<{width_id}} {statuses:<24} {row['company']} - {row['role']}")
        for e in row["events"]:
            if e.get("note"):
                print(f"    [{e['status']}] {e['note']}")


def _render_activity_rich(rows):
    from rich.text import Text

    console = render.console()
    width_id = max(len(row["id"]) for row in rows) + 2
    for row in rows:
        line = Text()
        line.append(f"{row['id']:<{width_id}} ")
        for i, status in enumerate(row["statuses"]):
            if i:
                line.append(", ")
            line.append(status, style=render.status_style(status))
        line.append(f"  {row['company']} - {row['role']}")
        console.print(line)
        for e in row["events"]:
            if e.get("note"):
                note_line = Text("    [")
                note_line.append(e["status"], style=render.status_style(e["status"]))
                note_line.append(f"] {e['note']}")
                console.print(note_line)


# Commands that do a load() -> mutate -> save() cycle and therefore need the write lock.
# Read-only commands are deliberately absent so they never block or wait on each other.
MUTATING_COMMANDS = {
    cmd_add,
    cmd_rescore,
    cmd_update_status,
    cmd_set_folder,
    cmd_set_listing,
    cmd_set_source,
    cmd_set_url,
    cmd_set_employer,
    cmd_set_facts,
    cmd_unset_fact,
    cmd_remove,
}
