"""`jobtracker init`: scaffold a fresh jobtracker data directory (see cli.py)."""
import importlib.resources
import sys
from pathlib import Path

from .store import MARKER_DIRNAME

# Directories that get an empty scaffold plus a README.md copied from templates/<dir>/README.md.
SCAFFOLD_DIRS = ["listings", "inbox", "applications", "anchors", "resume"]

# Top-level files copied verbatim from templates/<name>.
TOP_LEVEL_TEMPLATES = ["RUBRIC.md", "PREFERENCES.md", "SCORING.md", "corrections.md", "AGENTS.md"]


def scaffold(target: Path, force: bool = False) -> list[str]:
    """Scaffold a fresh jobtracker data directory at `target`, returning the list of created
    paths (as strings relative to `target`). Shared by the plain `init` command and the
    interactive `setup` wizard, so both produce an identical scaffold."""
    target = Path(target).resolve()
    marker = target / MARKER_DIRNAME

    if marker.exists() and not force:
        print(
            f"{target} is already a jobtracker data directory (found {MARKER_DIRNAME}/); "
            "nothing to do. Pass --force to reinitialize.",
            file=sys.stderr,
        )
        sys.exit(1)

    templates_root = importlib.resources.files("jobtracker").joinpath("templates")

    created = []

    marker.mkdir(parents=True, exist_ok=True)
    applications_json = marker / "applications.json"
    applications_json.write_text("[]\n")
    created.append(str(applications_json.relative_to(target)))

    for dirname in SCAFFOLD_DIRS:
        dest_dir = target / dirname
        dest_dir.mkdir(parents=True, exist_ok=True)
        readme_src = templates_root.joinpath(dirname, "README.md")
        readme_dest = dest_dir / "README.md"
        readme_dest.write_text(readme_src.read_text())
        created.append(str(readme_dest.relative_to(target)))

    # resume-reviewer needs its own rubric, same pattern as job-scorer's top-level RUBRIC.md.
    review_rubric_src = templates_root.joinpath("resume", "REVIEW_RUBRIC.md")
    review_rubric_dest = target / "resume" / "REVIEW_RUBRIC.md"
    review_rubric_dest.write_text(review_rubric_src.read_text())
    created.append(str(review_rubric_dest.relative_to(target)))

    for name in TOP_LEVEL_TEMPLATES:
        src = templates_root.joinpath(name)
        dest = target / name
        dest.write_text(src.read_text())
        created.append(str(dest.relative_to(target)))

    # Claude Code looks specifically for CLAUDE.md; symlink it to AGENTS.md so both names read
    # the same content with zero duplication. Relative target so the directory stays portable.
    claude_symlink = target / "CLAUDE.md"
    claude_symlink.unlink(missing_ok=True)
    claude_symlink.symlink_to("AGENTS.md")
    created.append(str(claude_symlink.relative_to(target)))

    return created


def cmd_init(args):
    target = Path(args.path or ".").resolve()
    created = scaffold(target, force=args.force)

    print(f"Initialized jobtracker data directory at {target}\n")
    print("Created:")
    for path in created:
        print(f"  {path}")
    print(
        "\nNext steps:\n"
        "  - cd into this directory and run `git init` yourself if you want version control.\n"
        "  - Install the Claude Code plugin if you haven't.\n"
        "  - Run `jobtracker setup` to walk through customization "
        "(hard gates, rubric weights, whether to build your resume evidence ledger now or later)."
    )
