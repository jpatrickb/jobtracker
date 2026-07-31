"""Persistence, record model, and id lookup for the job tracker (see cli.py).

Data-root resolution (data_root() / data_file() / etc. below) is deliberately lazy: it is resolved
and memoized on first actual use, not at module import time. `jobtracker init`/`setup` and
`jobtracker --help` must work from a location with no `.jobtracker/` marker anywhere in the parent
chain -- that's the whole point of `init`/`setup` -- so nothing at import time may probe the
filesystem for a data root. Every command that legitimately needs a data root (load/save, doctor,
listings, ...) still resolves it, and still exits with the same clear error, the first time it
actually asks for one.
"""
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import config

MARKER_DIRNAME = ".jobtracker"


def find_data_root(start=None, required=True):
    """Walk up from `start` (default cwd) looking for a `.jobtracker/` marker directory, the
    same way git walks up looking for `.git/`. This is what lets an installed, pip/uv-packaged
    `jobtracker` command find a user's data directory regardless of where the package itself lives
    on disk, or what directory under the data root the user happens to be in when they run it.
    Falls back to the default data root recorded by `jobtracker setup` (see config.py) if no
    marker is found anywhere in the parent chain, so daily use never requires `cd`-ing into a
    specific directory first -- the walk-up still lets someone maintain more than one data
    directory by simply running commands from inside the one they mean.

    `required=False` returns None instead of printing an error and exiting when no data root can
    be resolved -- used by the bare `jobtracker` (no subcommand) dispatch in cli.py to decide,
    without side effects, whether to launch the setup wizard or fall back to `list`."""
    start = Path(start or os.getcwd()).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / MARKER_DIRNAME).is_dir():
            return candidate

    default = config.read_default_data_root()
    if default is not None and (default / MARKER_DIRNAME).is_dir():
        return default

    if not required:
        return None

    print(
        f"error: no {MARKER_DIRNAME}/ found in {start} or any parent directory, and no default "
        "data directory is configured.\n"
        "Run 'jobtracker setup' to create one, or cd into an existing jobtracker data directory.",
        file=sys.stderr,
    )
    sys.exit(1)


_data_root = None
_data_file = None


def data_root():
    """Resolve and memoize the data root: JOBTRACKER_DATA_ROOT env var if set, else a
    marker-directory walk-up from cwd, else the default recorded by `jobtracker setup`
    (see find_data_root)."""
    global _data_root
    if _data_root is None:
        _data_root = (
            Path(os.environ["JOBTRACKER_DATA_ROOT"]).resolve()
            if os.environ.get("JOBTRACKER_DATA_ROOT")
            else find_data_root()
        )
    return _data_root


def data_file():
    """Resolve and memoize applications.json's path. JOBTRACKER_DATA_FILE lets
    verification/testing point at a throwaway copy instead of the live file; unset (the normal
    path) resolves to <data_root>/.jobtracker/applications.json."""
    global _data_file
    if _data_file is None:
        _data_file = (
            Path(os.environ["JOBTRACKER_DATA_FILE"]).resolve()
            if os.environ.get("JOBTRACKER_DATA_FILE")
            else data_root() / MARKER_DIRNAME / "applications.json"
        )
    return _data_file


def lock_file():
    df = data_file()
    return df.parent / f".{df.stem}.lock"


def listings_dir():
    return data_root() / "listings"


def inbox_dir():
    return data_root() / "inbox"


# Lifecycle order. "Scored" is the pool everything lands in; "Tailored" means a resume and cover
# letter exist in applications/<id>/ but nothing has been submitted yet, which is the distinction
# that matters most day to day. "Skipped" is a deliberate decision not to apply, and is kept
# separate from "Withdrawn" (pulling out after already applying) so the two don't get conflated.
STATUSES = [
    "Scored", "Tailored", "Applied", "Screening", "Interviewing", "Offer",
    "Skipped", "Rejected", "Withdrawn",
]
TERMINAL_STATUSES = {"Skipped", "Rejected", "Withdrawn"}
# Statuses that mean an application actually went out. Deliberately a set, not a position in
# STATUSES: "Skipped" sorts after "Offer" but means the opposite, and "Tailored" sorts before
# "Applied" but is pre-submission. Used for conversion stats and for deciding when a record
# ought to have an applications/<id>/ folder.
SUBMITTED_STATUSES = {"Applied", "Screening", "Interviewing", "Offer", "Rejected", "Withdrawn"}


def load():
    df = data_file()
    if not df.exists():
        return []
    return json.loads(df.read_text())


def save(records):
    """Write applications.json atomically, so a crash or a concurrent reader never
    sees a half-written file. Callers that mutate must hold the lock (see lock_for_write);
    this only guarantees the write itself is all-or-nothing."""
    df = data_file()
    payload = json.dumps(records, indent=2) + "\n"
    fd, tmp_path = tempfile.mkstemp(dir=str(df.parent), prefix=".applications.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, df)
    except BaseException:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def lock_for_write():
    """Take an exclusive cross-process lock covering a whole read-modify-write cycle.

    Every mutating subcommand does load() -> mutate -> save(), which is a lost-update race
    when several processes run at once (parallel scoring subagents each calling `add` will
    silently clobber each other's records). Each `track` invocation runs exactly one command
    and then exits, so holding the lock for the life of the process is both sufficient and
    simple. The handle is returned and kept alive by the caller; the OS releases the lock on
    process exit."""
    lf = lock_file()
    lf.parent.mkdir(parents=True, exist_ok=True)
    handle = open(lf, "w")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    return handle


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def make_id(records, company, role):
    base = f"{slugify(company)}-{slugify(role)}"
    existing_ids = {r["id"] for r in records}
    if base not in existing_ids:
        return base
    n = 2
    while f"{base}-{n}" in existing_ids:
        n += 1
    return f"{base}-{n}"


def record_was_submitted(r):
    """True if an application was actually sent for this record, at any point.

    Checks the whole status history, not just the current status, so a record that is now
    Rejected still counts as a real application. Records that jumped straight to a later stage
    without an explicit "Applied" entry (a recruiter reaching out, say) still count."""
    seen = {h["status"] for h in r.get("status_history", [])} | {r["status"]}
    return bool(seen & SUBMITTED_STATUSES)


def find(records, id_):
    for r in records:
        if r["id"] == id_:
            return r
    return None


def _is_interactive():
    """True only when both ends are a real terminal, so an automated invocation (piped/redirected
    stdin or stdout - exactly how an agent runs this command) never blocks waiting on a picker it
    has no way to render or drive."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def _format_candidate(r, width_id):
    return f"{r['id']:<{width_id}} {r['status']:<12} {r['score']:>3}/100  {r['company']} - {r['role']}"


def _print_candidates(candidates, query):
    """Deterministic, scriptable fallback: enumerate the matches so a human can retype a
    narrower query, without ever blocking on a picker."""
    label = f"'{query}'" if query else "(no query given)"
    print(f"{len(candidates)} record(s) match {label}; pass the exact id, or a narrower fragment:", file=sys.stderr)
    width_id = max(len(r["id"]) for r in candidates) + 2
    for i, r in enumerate(candidates, 1):
        print(f"  {i:>2}. {_format_candidate(r, width_id)}", file=sys.stderr)


def _pick_with_fzf(fzf_path, candidates, query):
    """Launch fzf seeded with `query`, one candidate summary per line over stdin. Returns the
    resolved record, the sentinel "cancelled" (Esc/Ctrl-C, fzf exit 130), or None on any other
    failure so the caller can fall back to the printed list."""
    width_id = max(len(r["id"]) for r in candidates) + 2
    lines = [_format_candidate(r, width_id) for r in candidates]
    try:
        result = subprocess.run(
            [fzf_path, "--height=40%", "--layout=reverse", "--query", query,
             "--prompt=track> ", "--header=id  status  score/100  company - role  (Esc to cancel)"],
            input="\n".join(lines), capture_output=True, text=True,
        )
    except OSError:
        return None
    if result.returncode == 130:
        return "cancelled"
    if result.returncode != 0 or not result.stdout.strip():
        return None
    selected_id = result.stdout.split(None, 1)[0]
    return find(candidates, selected_id)


def resolve_id(records, query):
    """Resolve a user-supplied id: the exact id, a partial/fuzzy fragment of id/company/role, or
    nothing at all (bare command). Exact match is a zero-cost first check, so a caller that
    already knows the real id (the common case for scripted/agent calls) pays no fuzzy-matching
    or fzf overhead and sees no behavior change from before this existed. An ambiguous or empty
    query falls through to an fzf picker when there's a real terminal to drive one, and to a
    deterministic numbered candidate list otherwise, so a non-interactive caller can never hang.

    Returns the resolved record, or None (having already printed a diagnostic) if nothing was
    resolved; callers just do `if not r: sys.exit(1)`.
    """
    if query:
        exact = find(records, query)
        if exact:
            return exact

    needle = (query or "").lower()
    candidates = [
        r for r in records
        if needle in r["id"].lower() or needle in r["company"].lower() or needle in r["role"].lower()
    ]

    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        print(f"No record matches '{query}'." if query else "No records to choose from.", file=sys.stderr)
        return None

    fzf_path = shutil.which("fzf") if _is_interactive() else None
    if fzf_path:
        picked = _pick_with_fzf(fzf_path, candidates, query or "")
        if picked == "cancelled":
            print("Selection cancelled.", file=sys.stderr)
            return None
        if picked is None:
            _print_candidates(candidates, query)
            return None
        return picked

    _print_candidates(candidates, query)
    return None


def get_field(record, field):
    """Resolve a top-level field (e.g. "score") or a "facts.<key>" dotted path."""
    if field.startswith("facts."):
        return (record.get("facts") or {}).get(field[len("facts."):])
    return record.get(field)
