"""Argparse wiring and entry point for the job tracker CLI."""
import argparse

from .store import STATUSES, lock_for_write, find_data_root
from .doctor import cmd_report, cmd_stale, cmd_doctor
from .commands import (
    cmd_add, cmd_rescore, cmd_update_status, cmd_set_folder, cmd_set_listing,
    cmd_set_source, cmd_set_url, cmd_set_employer, cmd_set_facts, cmd_unset_fact,
    cmd_remove, cmd_list, cmd_show, cmd_inbox, cmd_inbox_dupes, cmd_search, cmd_activity,
    MUTATING_COMMANDS,
)
from .init import cmd_init
from .wizard import cmd_setup


def main():
    parser = argparse.ArgumentParser(description="Job application tracker")
    parser.add_argument(
        "--plain", action="store_true",
        help="Force plain, uncolored output (also honored via the NO_COLOR env var). "
             "Must come before the subcommand, e.g. `jobtracker --plain list`.",
    )
    sub = parser.add_subparsers(dest="cmd", required=False)

    p_init = sub.add_parser("init", help="Scaffold a fresh jobtracker data directory")
    p_init.add_argument("path", nargs="?", default=None, help="Directory to initialize (default: current directory)")
    p_init.add_argument("--force", action="store_true", help="Reinitialize even if a .jobtracker/ marker already exists")
    p_init.set_defaults(func=cmd_init)

    p_setup = sub.add_parser(
        "setup", help="Interactive first-run wizard: pick a data directory, install agents/skills "
                       "for your coding agent"
    )
    p_setup.set_defaults(func=cmd_setup)

    p_add = sub.add_parser("add", help="Log a newly scored job (status starts at Scored)")
    p_add.add_argument("--company", required=True)
    p_add.add_argument("--role", required=True)
    p_add.add_argument("--score", type=int, required=True)
    p_add.add_argument("--band", required=True, help="e.g. 'Strong fit', 'REJECTED (gate: comp)'")
    p_add.add_argument("--url", default=None, help="Actual clickable URL to the posting, if you have one")
    p_add.add_argument("--source", default=None, help="Site/channel the listing came from, e.g. LinkedIn, Indeed, company careers page")
    p_add.add_argument("--listing-file", default=None, help="Path to a file with the raw posting text; saved verbatim to listings/<id>.md")
    p_add.add_argument("--facts", default=None, help="Inline JSON object of structured facts (pay, location, work format, etc.); only include what the posting states")
    p_add.add_argument("--facts-file", default=None, help="Path to a JSON file with structured facts; alternative to --facts that avoids shell-quoting")
    p_add.add_argument("--notes", default=None)
    p_add.add_argument("--scorer-version", default=None, help="Scoring stack version that produced this score; defaults to SCORING.md's current_version")
    p_add.add_argument("--force", action="store_true", help="Log a new attempt even if one is already tracked")
    p_add.set_defaults(func=cmd_add)

    p_rescore = sub.add_parser("rescore", help="Append a new scoring of an already-tracked job, keeping prior scores")
    p_rescore.add_argument("id", nargs="?", default=None, help="Full id, or a fragment of company/role to fuzzy-match (omit to pick interactively)")
    p_rescore.add_argument("--score", type=int, required=True)
    p_rescore.add_argument("--band", required=True, help="e.g. 'Strong fit', 'REJECTED (gate: comp)'")
    p_rescore.add_argument("--scorer-version", default=None, help="Version that produced this score; defaults to SCORING.md's current_version")
    p_rescore.add_argument("--note", default=None, help="Why it was rescored, or what moved")
    p_rescore.add_argument("--date", default=None, help="YYYY-MM-DD, defaults to today")
    p_rescore.add_argument("--force", action="store_true", help="Allow rescoring with the same version already on the record")
    p_rescore.set_defaults(func=cmd_rescore)

    p_status = sub.add_parser("update-status", help="Move an application to a new status")
    p_status.add_argument("id", nargs="?", default=None, help="Full id, or a fragment of company/role to fuzzy-match (omit to pick interactively)")
    p_status.add_argument("status", choices=STATUSES)
    p_status.add_argument("--note", default=None)
    p_status.add_argument("--date", default=None, help="YYYY-MM-DD, defaults to today")
    p_status.set_defaults(func=cmd_update_status)

    p_folder = sub.add_parser("set-folder", help="Link the applications/<job>/ folder")
    p_folder.add_argument("id", help="Full id, or a fragment of company/role to fuzzy-match")
    p_folder.add_argument("path")
    p_folder.set_defaults(func=cmd_set_folder)

    p_listing = sub.add_parser("set-listing", help="Save/replace the raw listing text from a file (writes listings/<id>.md)")
    p_listing.add_argument("id", help="Full id, or a fragment of company/role to fuzzy-match")
    p_listing.add_argument("path", help="Path to a file containing the raw job posting text")
    p_listing.set_defaults(func=cmd_set_listing)

    p_source = sub.add_parser("set-source", help="Set/update the source site for a record")
    p_source.add_argument("id", help="Full id, or a fragment of company/role to fuzzy-match")
    p_source.add_argument("source")
    p_source.set_defaults(func=cmd_set_source)

    p_url = sub.add_parser("set-url", help="Set/update the listing URL for a record (pass \"\" to clear)")
    p_url.add_argument("id", help="Full id, or a fragment of company/role to fuzzy-match")
    p_url.add_argument("url")
    p_url.set_defaults(func=cmd_set_url)

    p_employer = sub.add_parser("set-employer", help="Rename the company and/or role on a record (id stays the same)")
    p_employer.add_argument("id", nargs="?", default=None, help="Full id, or a fragment of company/role to fuzzy-match (omit to pick interactively)")
    p_employer.add_argument("--company", help="Corrected employer name")
    p_employer.add_argument("--role", help="Corrected role title")
    p_employer.set_defaults(func=cmd_set_employer)

    p_facts = sub.add_parser("set-facts", help="Merge structured facts (pay, location, work format, etc.) into a record")
    p_facts.add_argument("id", nargs="?", default=None, help="Full id, or a fragment of company/role to fuzzy-match (omit to pick interactively)")
    p_facts.add_argument("--facts", default=None, help="Inline JSON object to merge in")
    p_facts.add_argument("--facts-file", default=None, help="Path to a JSON file to merge in")
    p_facts.set_defaults(func=cmd_set_facts)

    p_unset_fact = sub.add_parser("unset-fact", help="Delete a single fact key from a record")
    p_unset_fact.add_argument("id", help="Full id, or a fragment of company/role to fuzzy-match")
    p_unset_fact.add_argument("key")
    p_unset_fact.set_defaults(func=cmd_unset_fact)

    p_remove = sub.add_parser("remove", help="Permanently delete a record and its listing file, if any")
    p_remove.add_argument("id", nargs="?", default=None, help="Full id, or a fragment of company/role to fuzzy-match (omit to pick interactively)")
    p_remove.add_argument("--force", action="store_true", help="Confirm the deletion (required)")
    p_remove.set_defaults(func=cmd_remove)

    p_list = sub.add_parser("list", help="List tracked applications")
    p_list.add_argument("--status", choices=STATUSES, default=None)
    p_list.add_argument("--company", default=None)
    p_list.add_argument(
        "--fact", action="append", default=[], metavar="KEY<op>VALUE",
        help="Filter by a structured fact. op is one of = != > < >= <=; numeric facts compare "
             "numerically, e.g. --fact 'pay_annual_min>=100000' or --fact work_format=Remote. "
             "Repeatable (AND). Quote args containing > or <.",
    )
    p_list.add_argument(
        "--sort", default=None, metavar="KEY",
        help="Sort by a top-level field (score, created_at, updated_at, company, ...) or a fact "
             "(facts.pay_annual_min). Defaults to status then score. Combine with --desc to reverse.",
    )
    p_list.add_argument("--desc", action="store_true", help="Reverse the --sort order")
    p_list.add_argument(
        "--fields", default=None, metavar="F,F,...",
        help="Comma-separated columns to print instead of the default summary line, e.g. "
             "'id,company,score,facts.work_format,facts.pay_annual_min'.",
    )
    p_list.add_argument("--scorer-version", default=None, metavar="vN", help="Only records scored by this version of the scoring stack")
    p_list.add_argument("--stale-score", action="store_true", help="Only records NOT scored by SCORING.md's current version (candidates for rescore)")
    p_list.add_argument("--json", action="store_true", help="Print the filtered/sorted records as a JSON array")
    p_list.set_defaults(func=cmd_list)

    p_inbox = sub.add_parser("inbox", help="List postings waiting to be scored in inbox/")
    p_inbox.set_defaults(func=cmd_inbox)

    p_inbox_dupes = sub.add_parser(
        "inbox-dupes", help="Flag likely-duplicate postings in inbox/ before they get scored"
    )
    p_inbox_dupes.add_argument(
        "--threshold", type=float, default=0.82,
        help="Title-similarity ratio (0-1) above which two inbox items are flagged as near-duplicates (default 0.82)",
    )
    p_inbox_dupes.set_defaults(func=cmd_inbox_dupes)

    p_search = sub.add_parser("search", help="Full-text search across listings/*.md bodies")
    p_search.add_argument("term", help="Text to search for (case-insensitive substring by default)")
    p_search.add_argument("--regex", action="store_true", help="Treat term as a regular expression instead of a literal substring")
    p_search.set_defaults(func=cmd_search)

    p_show = sub.add_parser("show", help="Show a full record, including status history")
    p_show.add_argument("id", nargs="?", default=None, help="Full id, or a fragment of company/role to fuzzy-match (omit to pick interactively)")
    p_show.add_argument("--json", action="store_true", help="Print the raw record as JSON instead of the formatted view")
    p_show.set_defaults(func=cmd_show)

    p_activity = sub.add_parser(
        "activity", help="Show status changes that happened on a given date (e.g. 'jobs applied to today')"
    )
    p_activity.add_argument(
        "date", nargs="?", default="today",
        help="YYYY-MM-DD, 'today' (default), or 'yesterday'",
    )
    p_activity.add_argument("--status", choices=STATUSES, default=None, help="Only show changes to this status, e.g. Applied")
    p_activity.add_argument("--json", action="store_true")
    p_activity.set_defaults(func=cmd_activity)

    p_report = sub.add_parser("report", help="Funnel counts, score distribution, source effectiveness, and staleness")
    p_report.set_defaults(func=cmd_report)

    p_stale = sub.add_parser("stale", help="List non-terminal records that haven't changed status in a while")
    p_stale.add_argument("--days", type=int, default=14, help="Threshold in days (default 14)")
    p_stale.set_defaults(func=cmd_stale)

    p_doctor = sub.add_parser("doctor", help="Check applications.json/listings/folder consistency")
    p_doctor.set_defaults(func=cmd_doctor)

    args = parser.parse_args()

    # Bare `jobtracker`, no subcommand: first run (no data root resolvable at all, by walk-up or
    # by the globally-remembered default) launches the setup wizard automatically, since there's
    # nothing useful `list` could show yet anyway. Once a data root exists, fall back to `list`
    # rather than printing generic argparse help -- that's the answer to "how's my search going"
    # people actually want from a bare invocation.
    if args.cmd is None:
        if find_data_root(required=False) is None:
            cmd_setup(args)
            return
        plain_flag = args.plain
        args = parser.parse_args(["list"])
        args.plain = plain_flag

    # Mutating commands serialize on an exclusive lock so concurrent invocations (e.g. several
    # scoring subagents running in parallel) can't lose each other's writes. Read-only commands,
    # and `init` (which doesn't touch applications.json and may run before a data root even
    # exists), skip it and stay fast; save() is atomic, so they never read a torn file.
    _lock = lock_for_write() if getattr(args, "func", None) in MUTATING_COMMANDS else None
    try:
        args.func(args)
    finally:
        if _lock is not None:
            _lock.close()
