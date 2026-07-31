"""`jobtracker setup`: interactive first-run wizard (see cli.py).

Also what bare `jobtracker` (no subcommand) launches automatically the first time it's run with
no default data directory configured -- see main() in cli.py.
"""
import re
import shutil
import subprocess
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt

from . import config
from .init import scaffold
from .store import MARKER_DIRNAME

DEFAULT_DATA_DIR = Path.home() / "JobTracker"


def cmd_setup(args=None):
    console = Console(no_color=bool(getattr(args, "plain", False)))

    console.print("[bold]jobtracker setup[/bold]\n")
    console.print("Let's get your job-search data directory set up.\n")

    target = _step_data_directory(console)
    _step_remember_globally(console, target)
    _step_hard_gates(console, target)
    kept_default_rubric = _step_rubric_weights(console, target)
    imported = _step_resume_import(console, target)
    plugin_wired, claude_found = _step_claude_plugin(console)

    _step_summary(console, target, kept_default_rubric, imported, plugin_wired, claude_found)


def _step_data_directory(console):
    target_str = Prompt.ask(
        "Where should your job-search data live?", default=str(DEFAULT_DATA_DIR)
    )
    target = Path(target_str).expanduser().resolve()
    marker = target / MARKER_DIRNAME

    if marker.is_dir():
        console.print(f"\n{target} is already a jobtracker data directory.")
        reinit = Confirm.ask(
            "Reinitialize it? (resets scaffolded files back to their templates; your "
            ".jobtracker/applications.json is untouched either way)",
            default=False,
        )
        if reinit:
            created = scaffold(target, force=True)
            console.print(f"\nReinitialized {target}.")
        else:
            created = []
            console.print(f"\nUsing {target} as-is.")
    else:
        created = scaffold(target)
        console.print(f"\nCreated a fresh jobtracker data directory at {target}.")

    if created:
        console.print("Created:")
        for path in created:
            console.print(f"  {path}")

    return target


def _step_remember_globally(console, target):
    config.write_default_data_root(target)
    console.print(
        f"\nRemembered {target} as your default data directory "
        f"({config.config_path()}), so bare `jobtracker` works from anywhere now.\n"
    )


def _step_hard_gates(console, target):
    console.print("[bold]Hard gates[/bold] -- postings that fail any of these get auto-rejected "
                   "before scoring.\n")

    gates = []

    if Confirm.ask("Do you have a minimum compensation requirement?", default=False):
        amount = IntPrompt.ask("What's the minimum? (just the number, e.g. 150000 or 75)")
        basis = Prompt.ask(
            "Is that an annual salary or an hourly rate?",
            choices=["annual", "hourly"], default="annual",
        )
        if basis == "annual":
            condition = f"base salary disclosed AND < ${amount:,}"
        else:
            condition = f"hourly rate disclosed AND < ${amount:,}/hr"
        gates.append({
            "name": "Compensation floor",
            "condition": condition,
            "reject_message": "Below comp floor",
        })

    if Confirm.ask("\nDo you have a location or remote-work requirement?", default=False):
        description = Prompt.ask(
            "Describe it in a sentence (e.g. 'must be fully remote, or onsite/hybrid within "
            "commuting distance of Austin, TX')"
        )
        gates.append({
            "name": "Location",
            "condition": description,
            "reject_message": "Location doesn't work",
        })

    console.print()
    while Confirm.ask(
        "Any other hard requirement that should auto-reject a posting (visa sponsorship, "
        "security clearance, something else)?",
        default=False,
    ):
        name = Prompt.ask("Short name for this requirement (e.g. 'Visa sponsorship')")
        condition = Prompt.ask("One-sentence condition that should cause an auto-reject")
        gates.append({
            "name": name,
            "condition": condition,
            "reject_message": f"Fails: {name}",
        })

    _write_hard_gates(target, gates)
    if gates:
        console.print(f"\nWrote {len(gates)} hard gate(s) to PREFERENCES.md.")
    else:
        console.print(
            "\nNo hard gates set -- left the illustrative placeholder examples in PREFERENCES.md "
            "(clearly marked as such). Edit them there whenever you're ready."
        )


def _render_hard_gates_body(gates):
    if gates:
        entries = "\n".join(
            f'- name: {g["name"]}\n'
            f'  condition: {g["condition"]}\n'
            f'  reject_message: "{g["reject_message"]}"'
            for g in gates
        )
        return (
            f"{entries}\n\n"
            "Add, remove, or edit these freely as your requirements change -- this list isn't "
            "limited to what you entered during `jobtracker setup` (minimum years of experience, "
            "employment types you won't consider, industries you rule out, company size "
            "floors/ceilings, and so on all fit here too).\n"
        )
    return (
        "<!-- No hard gates were set during `jobtracker setup`. The two entries below are "
        "illustrative placeholders, not real defaults -- edit or delete them to match your actual "
        "requirements. -->\n\n"
        "- name: Compensation floor\n"
        "  condition: base salary disclosed AND < $X\n"
        '  reject_message: "Below comp floor"\n'
        "- name: Location\n"
        "  condition: not remote AND not in [your metro]\n"
        '  reject_message: "Location doesn\'t work"\n\n'
        "Replace `$X` and `[your metro]` with real values, and add whatever other gates matter to "
        "you (e.g. minimum years of experience required that you don't meet, employment types you "
        "won't consider, industries you rule out, company size floors/ceilings, visa sponsorship "
        "requirements).\n"
    )


def _write_hard_gates(target, gates):
    prefs_path = target / "PREFERENCES.md"
    text = prefs_path.read_text()

    heading = "## Hard gates (reject before scoring)\n"
    start = text.find(heading)
    if start == -1:
        # Heading not found (unexpected custom PREFERENCES.md) -- don't guess, leave it alone.
        return

    intro = (
        "\nAny posting failing ANY gate below is rejected without being scored.\n"
        "Keep each gate's `condition` phrased so a scoring agent can evaluate it directly against "
        "a posting's text/facts, and keep `reject_message` short, it's what gets logged as the "
        "rejection band.\n\n"
    )

    next_heading = text.find("\n## ", start + len(heading))
    end = next_heading + 1 if next_heading != -1 else len(text)

    new_section = heading + intro + _render_hard_gates_body(gates)
    prefs_path.write_text(text[:start] + new_section + text[end:])


def _step_rubric_weights(console, target):
    console.print("\n[bold]Rubric weights[/bold]\n")
    rubric_text = (target / "RUBRIC.md").read_text()
    dims = re.findall(r"^### (.+?)\s*\(weight: (\d+)%\)", rubric_text, re.MULTILINE)
    if dims:
        for name, weight in dims:
            console.print(f"  {name} -- {weight}%")
    else:
        console.print("  (couldn't find dimension headings in RUBRIC.md to summarize)")

    keep = Confirm.ask("\nKeep these defaults for now?", default=True)
    if not keep:
        console.print(
            "No problem -- edit RUBRIC.md directly whenever you're ready, or revisit it through "
            "the job-scorer agent's feedback loop later."
        )
    return keep


def _step_resume_import(console, target):
    console.print(
        "\n[bold]Resume / proof-of-work import[/bold]\n\n"
        "Do you have an existing resume, LinkedIn export, or other work-history document to "
        "import as a starting point?"
    )
    imported = []
    path_str = Prompt.ask("Enter a file path, or press Enter to skip", default="")

    while path_str:
        src = Path(path_str).expanduser()
        if not src.is_file():
            console.print(f"[yellow]No file found at {src}. Try again, or press Enter to skip.[/yellow]")
            path_str = Prompt.ask("Enter a file path, or press Enter to skip", default="")
            continue

        imports_dir = target / "resume" / "imports"
        imports_dir.mkdir(parents=True, exist_ok=True)
        dest = imports_dir / src.name
        shutil.copy2(src, dest)
        imported.append(str(dest.relative_to(target)))
        console.print(f"Imported -> {dest.relative_to(target)}")

        if not Confirm.ask("Add another?", default=False):
            break
        path_str = Prompt.ask("Enter another file path, or press Enter to skip", default="")

    return imported


CLAUDE_COMMANDS = [
    ["plugin", "marketplace", "add", "jpatrickb/jobtracker"],
    ["plugin", "install", "jobtracker@jobtracker-marketplace"],
]


def _step_claude_plugin(console):
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return False, False

    console.print("\n[bold]Claude Code plugin[/bold]\n")
    if not Confirm.ask("Set up the Claude Code plugin now?", default=True):
        console.print("Skipping. Run these yourself whenever you're ready:")
        for cmd_args in CLAUDE_COMMANDS:
            console.print(f"  claude {' '.join(cmd_args)}")
        return False, True

    try:
        for cmd_args in CLAUDE_COMMANDS:
            result = subprocess.run(
                [claude_bin, *cmd_args], capture_output=True, text=True, timeout=120
            )
            if result.stdout.strip():
                console.print(result.stdout.strip())
            if result.stderr.strip():
                console.print(result.stderr.strip())
            if result.returncode != 0:
                raise RuntimeError(f"`claude {' '.join(cmd_args)}` exited {result.returncode}")
    except Exception as exc:
        console.print(f"[yellow]Couldn't run the plugin commands automatically ({exc}).[/yellow]")
        console.print("Run these yourself:")
        for cmd_args in CLAUDE_COMMANDS:
            console.print(f"  claude {' '.join(cmd_args)}")
        return False, True

    console.print("Claude Code plugin installed.")
    return True, True


def _step_summary(console, target, kept_default_rubric, imported, plugin_wired, claude_found):
    console.print("\n[bold]Summary[/bold]\n")
    console.print(f"  Data directory: {target}")
    console.print(f"  Remembered globally: yes ({config.config_path()})")
    console.print("  Hard gates: see PREFERENCES.md")
    if imported:
        console.print(f"  Imported {len(imported)} file(s): {', '.join(imported)}")
    else:
        console.print("  Resume import: skipped")
    if plugin_wired:
        console.print("  Claude Code plugin: installed")
    elif claude_found:
        console.print("  Claude Code plugin: not installed (see the commands printed above)")
    else:
        console.print(
            "  Claude Code plugin: `claude` not found on PATH -- once installed, run:\n"
            "    claude plugin marketplace add jpatrickb/jobtracker\n"
            "    claude plugin install jobtracker@jobtracker-marketplace"
        )

    console.print(
        "\nStill worth knowing about (documented defaults -- edit RUBRIC.md/AGENTS.md directly "
        "to change them):"
    )
    if kept_default_rubric:
        console.print("  - Rubric weights: kept at the scaffolded defaults.")
    console.print("  - Resume length target: 2 pages.")
    console.print("  - Cover-letter policy: only written when the employer asks for one, or you do.")

    console.print(
        "\n[bold]Next step:[/bold] open Claude Code in this directory (or anywhere, now that it's "
        "your default) and run the `resume-onboarding` skill to build your evidence ledger"
        + (", using what you imported just now." if imported else ".")
    )
