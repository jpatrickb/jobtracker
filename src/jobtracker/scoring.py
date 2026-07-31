"""Scoring-stack version bookkeeping for the job tracker (see cli.py)."""
import re
import subprocess
import sys

from . import store

# The scoring stack (the job-scorer agent + RUBRIC.md + PREFERENCES.md + anchors/ + corrections.md)
# is versioned as a whole in SCORING.md, because any of those files can move a score. Every score
# carries the version that produced it so cross-version comparisons can be caught rather than
# silently ranked against each other.
SCORING_VERSION_RE = re.compile(r"^current_version:\s*(v\d+)\s*$", re.M)
# The files that together produce a score. Editing any of them can move numbers, so doctor checks
# whether they've changed since SCORING.md was last touched: a bump that nobody remembers to make is
# worse than no versioning at all, because the version label then actively lies.
#
# The job-scorer agent itself is NOT in this list. It's plugin-owned and lives outside DATA_ROOT
# (installed separately via the Claude Code plugin system), so this git-log-based drift check has
# no path under DATA_ROOT to look at and can't see when it changes. The plugin is versioned on its
# own; SCORING.md's changelog is still the place to note a score-moving change to it by hand.
SCORING_STACK_PATHS = [
    "RUBRIC.md",
    "PREFERENCES.md",
    "anchors",
    "corrections.md",
]


def current_scoring_version():
    """The scorer version currently declared in SCORING.md, or None if it can't be read."""
    scoring_file = store.data_root() / "SCORING.md"
    if not scoring_file.exists():
        return None
    match = SCORING_VERSION_RE.search(scoring_file.read_text())
    return match.group(1) if match else None


def _git(*args):
    """Run a git command in the repo, returning stdout or None if git isn't usable here."""
    try:
        result = subprocess.run(
            ["git", *args], cwd=str(store.data_root()), capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None


def check_scoring_drift():
    """Advisories for scoring-stack files edited without a corresponding SCORING.md update.

    This is the backstop for the rule that whoever edits the rubric, preferences, anchors, or
    corrections has to decide whether the change can move a score, and either bump
    current_version or record in SCORING.md that it can't. Advisory rather than fatal, because
    a genuinely cosmetic edit shouldn't be able to wedge doctor into permanent failure."""
    data_root = store.data_root()
    if not (data_root / ".git").exists() or _git("rev-parse", "--git-dir") is None:
        return []

    def last_commit_ts(path):
        out = _git("log", "-1", "--format=%ct", "--", path)
        return int(out.strip()) if out and out.strip() else None

    def is_dirty(path):
        out = _git("status", "--porcelain", "--", path)
        return bool(out and out.strip())

    advisories = []
    scoring_ts = last_commit_ts("SCORING.md")
    scoring_dirty = is_dirty("SCORING.md")

    for path in SCORING_STACK_PATHS:
        if not (data_root / path).exists():
            continue
        if is_dirty(path) and not scoring_dirty:
            advisories.append(f"{path} has uncommitted changes but SCORING.md does not")
            continue
        path_ts = last_commit_ts(path)
        if path_ts is not None and scoring_ts is not None and path_ts > scoring_ts:
            advisories.append(f"{path} was committed after SCORING.md was last updated")
    return advisories


def scoring_version_number(version):
    """The numeric part of a 'vN' label, or None if it isn't one.

    Versions are monotonic integers, so "is this record behind?" is a numeric comparison, not an
    inequality: a record stamped with a version NEWER than SCORING.md declares is an anomaly for
    doctor to flag, not something to sweep into a rescore queue."""
    if not version:
        return None
    match = re.fullmatch(r"v(\d+)", str(version).strip())
    return int(match.group(1)) if match else None


def score_is_behind(r, current_number):
    """True if this record was scored by an older version than the current one (or none at all)."""
    if current_number is None:
        return False
    number = scoring_version_number(r.get("scorer_version"))
    return number is None or number < current_number


def resolve_scorer_version(explicit):
    """The version to stamp on a score: an explicit --scorer-version, else SCORING.md's."""
    version = explicit or current_scoring_version()
    if not version:
        print(
            "No scorer version available: pass --scorer-version vN, or declare a "
            "'current_version: vN' line in SCORING.md.",
            file=sys.stderr,
        )
        sys.exit(1)
    return version


def score_entry(score, band, version, when, note=""):
    return {"score": score, "band": band, "version": version, "date": when, "note": note}
