"""Terminal-aware, colorized rendering for human use.

Every entry point here is a no-op (is_pretty() returns False) for any non-tty invocation, so
agents (Bash tool), smoke_test.sh, and the --json paths are structurally unaffected: they never
reach the `import rich` line at all, because sys.stdout.isatty() is already False for them. See
the render module's callers in commands.py and doctor.py for the shape/plain/rich split each
command follows.
"""
import os
import sys

# Score bands per RUBRIC.md's "Score bands (headline 0 to 100)" section.
SCORE_BANDS = [
    (90, "bold green"),
    (75, "green"),
    (60, "cyan"),
    (40, "yellow"),
    (0, "red"),
]

# One entry per store.STATUSES. Chosen using store.TERMINAL_STATUSES / store.SUBMITTED_STATUSES
# as the basis: Scored is the neutral starting pool; Tailored is built but not yet submitted;
# Applied/Screening/Interviewing are submitted and still in motion; Offer is the positive outcome;
# Skipped is a deliberate non-submission (not a failure); Rejected/Withdrawn are both terminal
# submitted outcomes but distinct in kind (external verdict vs. the applicant's own call).
STATUS_STYLES = {
    "Scored": "white",
    "Tailored": "yellow",
    "Applied": "cyan",
    "Screening": "blue",
    "Interviewing": "bright_blue",
    "Offer": "bold green",
    "Skipped": "dim",
    "Rejected": "red",
    "Withdrawn": "magenta",
}

_pretty_cache = None  # memoize the (tty-check + rich-import) decision per process


def is_pretty(args) -> bool:
    """Whether to use rich rendering: a real terminal, no NO_COLOR/--plain override, and rich
    actually importable. False for every agent/piped/redirected invocation by construction."""
    global _pretty_cache
    if _pretty_cache is not None:
        return _pretty_cache
    if getattr(args, "plain", False) or os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        _pretty_cache = False
        return False
    try:
        import rich  # noqa: F401  (import used only to prove availability)
    except ImportError:
        print(
            "rich not installed for this interpreter; falling back to plain output.",
            file=sys.stderr,
        )
        _pretty_cache = False
        return False
    _pretty_cache = True
    return True


def console():
    """Call only after is_pretty() has returned True."""
    from rich.console import Console

    return Console()


def text(value, style=None):
    """Wrap a value as a literal rich Text span (never markup-parsed). Job-posting data can
    contain '[' / ']' incidentally, which rich's default markup parsing would otherwise choke on
    or misrender if passed as a plain string to Table/Console."""
    from rich.text import Text

    return Text("" if value is None else str(value), style=style)


def status_style(status):
    return STATUS_STYLES.get(status, "white")


def score_style(score, band=None):
    if band and "REJECTED" in band.upper():
        return "bold red"
    for threshold, style in SCORE_BANDS:
        if score >= threshold:
            return style
    return "red"
