"""Doctor/report/staleness analytics for the job tracker (see cli.py)."""
import sys
from datetime import date

from . import store
from .store import STATUSES, TERMINAL_STATUSES, SUBMITTED_STATUSES, load, record_was_submitted
from .facts import REQUIRED_FACT_KEYS
from .scoring import current_scoring_version, check_scoring_drift, scoring_version_number, score_is_behind
from .listings import check_duplicate_listing_bodies, parse_listing_frontmatter
from . import render


def days_in_status(record, today=None):
    today = today or date.today()
    last_change = record["status_history"][-1]["date"] if record.get("status_history") else record["updated_at"]
    return (today - date.fromisoformat(last_change)).days


def cmd_report(args):
    records = load()
    if not records:
        print("No records.")
        return

    shaped = _shape_report(records)
    if render.is_pretty(args):
        _render_report_rich(shaped)
    else:
        _render_report_plain(shaped)


def _shape_report(records):
    funnel = [(status, sum(1 for r in records if r["status"] == status)) for status in STATUSES]

    scores = [r["score"] for r in records if isinstance(r.get("score"), (int, float))]
    score_stats = None
    if scores:
        s = sorted(scores)
        n = len(s)
        median = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
        score_stats = {"avg": sum(scores) / n, "median": median, "min": min(scores), "max": max(scores), "n": n}

    # Scores are only comparable within a version, so surface the split before anyone reads the
    # distribution above or the ranking in `list` as if it were one measurement.
    current = current_scoring_version()
    by_version_map = {}
    for r in records:
        by_version_map.setdefault(r.get("scorer_version") or "(unversioned)", []).append(r)
    by_version = []
    for version, rs in sorted(by_version_map.items()):
        avg = sum(x["score"] for x in rs) / len(rs)
        by_version.append({"version": version, "n": len(rs), "avg": avg, "is_current": version == current})
    mixed = len(by_version_map) > 1

    # Reported regardless of whether versions are mixed: right after a bump every record is behind,
    # which is uniform and therefore silent under a mixed-versions-only check, yet is exactly when
    # knowing what needs rescoring matters most.
    current_number = scoring_version_number(current)
    behind_records = [r for r in records if score_is_behind(r, current_number)]
    behind = None
    if behind_records:
        active_behind = [r for r in behind_records if r["status"] not in TERMINAL_STATUSES]
        behind = {"count": len(behind_records), "active_count": len(active_behind), "current": current}

    by_source_map = {}
    for r in records:
        by_source_map.setdefault(r.get("source") or "(unknown)", []).append(r)
    by_source = []
    for src, rs in sorted(by_source_map.items(), key=lambda kv: -len(kv[1])):
        avg_score = sum(x["score"] for x in rs) / len(rs)
        # Check history rather than current status: a record can be Rejected or Withdrawn now and
        # still have been a real application. Deliberately excludes Skipped (decided against) and
        # Tailored (built but never sent), neither of which is a conversion.
        converted = sum(1 for x in rs if record_was_submitted(x))
        by_source.append({
            "source": src, "n": len(rs), "avg_score": avg_score,
            "converted": converted, "total": len(rs), "pct": converted / len(rs) * 100,
        })

    active = [r for r in records if r["status"] not in TERMINAL_STATUSES]
    days_rows = None
    if active:
        aged = sorted(((days_in_status(r), r) for r in active), key=lambda x: -x[0])
        days_rows = [{"id": r["id"], "status": r["status"], "days": days} for days, r in aged]

    return {
        "funnel": funnel, "total": len(records),
        "score_stats": score_stats,
        "by_version": by_version, "mixed": mixed,
        "behind": behind,
        "by_source": by_source,
        "days_in_status": days_rows,
    }


def _render_report_plain(s):
    print("Funnel:")
    for status, count in s["funnel"]:
        print(f"  {status:<14} {count}")
    print(f"  {'Total':<14} {s['total']}")

    if s["score_stats"]:
        st = s["score_stats"]
        print(f"\nScore: avg {st['avg']:.1f}, median {st['median']:.1f}, range {st['min']}-{st['max']} (n={st['n']})")

    print("\nBy scorer version:")
    for v in s["by_version"]:
        marker = "  <- current" if v["is_current"] else ""
        print(f"  {v['version']:<16} n={v['n']:<3} avg_score={v['avg']:5.1f}{marker}")
    if s["mixed"]:
        print(
            f"  WARNING: scores span {len(s['by_version'])} versions. Cross-version scores are not "
            "comparable; the distribution above and `list` ranking mix instruments."
        )
    if s["behind"]:
        b = s["behind"]
        print(
            f"  {b['count']} record(s) behind {b['current']}, {b['active_count']} of them non-terminal. "
            "See: jobtracker list --stale-score"
        )

    print("\nBy source (conversion = an application was actually submitted):")
    for src in s["by_source"]:
        print(f"  {src['source']:<30} n={src['n']:<3} avg_score={src['avg_score']:5.1f}  converted={src['converted']}/{src['total']} ({src['pct']:.0f}%)")

    if s["days_in_status"]:
        print("\nDays in current status (non-terminal, oldest first):")
        for row in s["days_in_status"]:
            days = row["days"]
            print(f"  {row['id']:<50} {row['status']:<14} {days} day{'s' if days != 1 else ''}")


def _render_report_rich(s):
    from rich.table import Table

    console = render.console()

    console.print("Funnel:", style="bold")
    table = Table(box=None, show_header=False, pad_edge=False)
    table.add_column("status", no_wrap=True)
    table.add_column("count", justify="right", no_wrap=True)
    for status, count in s["funnel"]:
        table.add_row(render.text(status, style=render.status_style(status)), render.text(count))
    table.add_row(render.text("Total", style="bold"), render.text(s["total"], style="bold"))
    console.print(table)

    if s["score_stats"]:
        st = s["score_stats"]
        console.print()
        console.print(render.text(
            f"Score: avg {st['avg']:.1f}, median {st['median']:.1f}, range {st['min']}-{st['max']} (n={st['n']})"
        ))

    console.print()
    console.print("By scorer version:", style="bold")
    table = Table(box=None, show_header=False, pad_edge=False)
    table.add_column("version", no_wrap=True)
    table.add_column("n", justify="right", no_wrap=True)
    table.add_column("avg_score", justify="right", no_wrap=True)
    table.add_column("", no_wrap=True)
    for v in s["by_version"]:
        table.add_row(
            render.text(v["version"], style="bold" if v["is_current"] else None),
            render.text(v["n"]),
            render.text(f"{v['avg']:.1f}"),
            render.text("<- current" if v["is_current"] else "", style="dim"),
        )
    console.print(table)
    if s["mixed"]:
        console.print(render.text(
            f"  WARNING: scores span {len(s['by_version'])} versions. Cross-version scores are not "
            "comparable; the distribution above and `list` ranking mix instruments."
        ), style="bold yellow")
    if s["behind"]:
        b = s["behind"]
        console.print(render.text(
            f"  {b['count']} record(s) behind {b['current']}, {b['active_count']} of them non-terminal. "
            "See: jobtracker list --stale-score"
        ), style="yellow")

    console.print()
    console.print("By source (conversion = an application was actually submitted):", style="bold")
    table = Table(box=None, show_header=False, pad_edge=False, expand=True)
    table.add_column("source", ratio=1, overflow="ellipsis", no_wrap=True)
    table.add_column("n", width=5, justify="right", no_wrap=True)
    table.add_column("avg_score", width=10, justify="right", no_wrap=True)
    table.add_column("converted", width=16, no_wrap=True)
    for src in s["by_source"]:
        table.add_row(
            render.text(src["source"]),
            render.text(src["n"]),
            render.text(f"{src['avg_score']:.1f}"),
            render.text(
                f"{src['converted']}/{src['total']} ({src['pct']:.0f}%)",
                style="green" if src["pct"] >= 50 else None,
            ),
        )
    console.print(table)

    if s["days_in_status"]:
        console.print()
        console.print("Days in current status (non-terminal, oldest first):", style="bold")
        table = Table(box=None, show_header=False, pad_edge=False, expand=True)
        table.add_column("id", style="dim", ratio=1, overflow="ellipsis", no_wrap=True)
        table.add_column("status", width=14, no_wrap=True)
        table.add_column("days", width=10, no_wrap=True)
        for row in s["days_in_status"]:
            days = row["days"]
            table.add_row(
                render.text(row["id"]),
                render.text(row["status"], style=render.status_style(row["status"])),
                render.text(f"{days} day{'s' if days != 1 else ''}"),
            )
        console.print(table)


def cmd_stale(args):
    records = load()
    stale = [
        (days_in_status(r), r) for r in records
        if r["status"] not in TERMINAL_STATUSES and days_in_status(r) >= args.days
    ]
    if not stale:
        print(f"Nothing has gone {args.days}+ days without a status change.")
        return
    stale.sort(key=lambda x: -x[0])
    shaped = [{"id": r["id"], "status": r["status"], "days": days} for days, r in stale]
    if render.is_pretty(args):
        _render_stale_rich(shaped, args.days)
    else:
        _render_stale_plain(shaped, args.days)
    sys.exit(1)


def _render_stale_plain(rows, days_threshold):
    print(f"{len(rows)} record(s) gone {days_threshold}+ days without a status change:")
    for row in rows:
        days = row["days"]
        print(f"  {row['id']:<50} {row['status']:<14} {days} day{'s' if days != 1 else ''}")


def _render_stale_rich(rows, days_threshold):
    from rich.table import Table

    console = render.console()
    console.print(
        render.text(f"{len(rows)} record(s) gone {days_threshold}+ days without a status change:"),
        style="bold",
    )
    table = Table(box=None, show_header=False, pad_edge=False, expand=True)
    table.add_column("id", style="dim", ratio=1, overflow="ellipsis", no_wrap=True)
    table.add_column("status", width=14, no_wrap=True)
    table.add_column("days", width=10, no_wrap=True)
    for row in rows:
        days = row["days"]
        table.add_row(
            render.text(row["id"]),
            render.text(row["status"], style=render.status_style(row["status"])),
            render.text(f"{days} day{'s' if days != 1 else ''}"),
        )
    console.print(table)


def check_score_history(r):
    """Structural problems with a record's scoring provenance. Completeness (is every fact filled
    in?) is deliberately NOT checked here; that's an advisory, not a broken record."""
    problems = []
    history = r.get("score_history")
    if not history:
        problems.append(f"{r['id']}: no score_history (every score needs the version that produced it)")
        return problems
    last = history[-1]
    if r.get("score") != last["score"] or r.get("band") != last["band"]:
        problems.append(
            f"{r['id']}: score/band is {r.get('score')}/{r.get('band')!r} but the last score_history "
            f"entry is {last['score']}/{last['band']!r}"
        )
    if r.get("scorer_version") != last.get("version"):
        problems.append(
            f"{r['id']}: scorer_version is {r.get('scorer_version')!r} but the last score_history "
            f"entry was scored by {last.get('version')!r}"
        )
    dates = [e.get("date", "") for e in history]
    if dates != sorted(dates):
        problems.append(f"{r['id']}: score_history dates are out of order ({', '.join(dates)})")
    return problems


def cmd_doctor(args):
    records = load()
    problems = []
    advisories = []
    current_number = scoring_version_number(current_scoring_version())
    # Tailored is the one pre-submission status that still expects a folder, since the whole point
    # of it is that the documents exist. Skipped never expects one.
    folder_expected = SUBMITTED_STATUSES | {"Tailored"}

    for r in records:
        if r.get("listing_file"):
            path = store.data_root() / r["listing_file"]
            if not path.exists():
                problems.append(f"{r['id']}: listing_file '{r['listing_file']}' does not exist")
            else:
                fm = parse_listing_frontmatter(path)
                if fm is None:
                    problems.append(f"{r['id']}: {r['listing_file']} has no parseable frontmatter")
                else:
                    for key, value in (r.get("facts") or {}).items():
                        expected = "" if value is None else str(value)
                        actual = fm.get(key)
                        if actual is None:
                            problems.append(f"{r['id']}: fact '{key}' missing from {r['listing_file']} frontmatter")
                        elif actual != expected:
                            problems.append(
                                f"{r['id']}: fact '{key}' is {value!r} in applications.json but "
                                f"{actual!r} in {r['listing_file']}"
                            )

        if r.get("folder"):
            path = store.data_root() / r["folder"]
            if not path.exists():
                problems.append(f"{r['id']}: folder '{r['folder']}' does not exist")
        elif r["status"] in folder_expected:
            problems.append(f"{r['id']}: status is '{r['status']}' but no folder is linked (see set-folder)")

        problems.extend(check_score_history(r))

        # A score stamped with a version newer than SCORING.md declares means either the bump was
        # never committed or the version was typo'd; either way the label points at nothing.
        version_number = scoring_version_number(r.get("scorer_version"))
        if current_number is not None and version_number is not None and version_number > current_number:
            problems.append(
                f"{r['id']}: scored by {r['scorer_version']}, which is ahead of SCORING.md's "
                f"current_version (v{current_number})"
            )

        missing = [k for k in REQUIRED_FACT_KEYS if k not in (r.get("facts") or {})]
        if missing:
            advisories.append(f"{r['id']}: required fact(s) never captured: {', '.join(missing)}")

    dupe_problems, dupe_advisories = check_duplicate_listing_bodies(records)
    problems.extend(dupe_problems)
    advisories.extend(dupe_advisories)

    drift = check_scoring_drift()
    shaped = {
        "n_records": len(records),
        "problems": problems,
        "advisories": advisories,
        "drift": drift,
        "current": current_scoring_version() or "?",
    }
    if render.is_pretty(args):
        _render_doctor_rich(shaped)
    else:
        _render_doctor_plain(shaped)

    if problems:
        sys.exit(1)


def _render_doctor_plain(s):
    if s["problems"]:
        print(f"{len(s['problems'])} issue(s) found across {s['n_records']} records:")
        for p in s["problems"]:
            print(f"  - {p}")
    else:
        print(f"All {s['n_records']} records are structurally consistent.")

    # Advisories are data gaps, not corruption: a posting genuinely may not state a salary. They're
    # reported but never fail the exit code, so doctor stays usable as a real integrity check.
    if s["advisories"]:
        print(f"\n{len(s['advisories'])} record(s) with incomplete facts (advisory, not a failure):")
        for a in s["advisories"]:
            print(f"  - {a}")
        print("  Set the value, or null to record that the posting doesn't disclose it.")

    if s["drift"]:
        print(f"\nScoring stack changed since SCORING.md was last updated (current: {s['current']}):")
        for d in s["drift"]:
            print(f"  - {d}")
        print(
            "  If the change can move a score, bump current_version in SCORING.md and add a "
            "changelog entry.\n"
            "  If it genuinely cannot (typo, formatting), note that under the current version so "
            "the decision is recorded either way."
        )


def _render_doctor_rich(s):
    console = render.console()
    if s["problems"]:
        console.print(
            render.text(f"{len(s['problems'])} issue(s) found across {s['n_records']} records:"),
            style="bold red",
        )
        for p in s["problems"]:
            console.print(render.text(f"  - {p}"), style="red")
    else:
        console.print(
            render.text(f"All {s['n_records']} records are structurally consistent."),
            style="bold green",
        )

    if s["advisories"]:
        console.print()
        console.print(
            render.text(f"{len(s['advisories'])} record(s) with incomplete facts (advisory, not a failure):"),
            style="bold yellow",
        )
        for a in s["advisories"]:
            console.print(render.text(f"  - {a}"), style="yellow")
        console.print(
            render.text("  Set the value, or null to record that the posting doesn't disclose it."),
            style="dim",
        )

    if s["drift"]:
        console.print()
        console.print(
            render.text(f"Scoring stack changed since SCORING.md was last updated (current: {s['current']}):"),
            style="bold cyan",
        )
        for d in s["drift"]:
            console.print(render.text(f"  - {d}"), style="cyan")
        console.print(render.text(
            "  If the change can move a score, bump current_version in SCORING.md and add a "
            "changelog entry.\n"
            "  If it genuinely cannot (typo, formatting), note that under the current version so "
            "the decision is recorded either way."
        ), style="dim")
