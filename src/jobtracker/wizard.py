"""`jobtracker setup`: interactive first-run wizard (see cli.py).

Also what bare `jobtracker` (no subcommand) launches automatically the first time it's run with
no default data directory configured -- see main() in cli.py.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import IntPrompt, Prompt

from . import config
from .curses_ui import prompt_choice
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
    agents_installed = _step_agent_install(console, target)

    _step_summary(console, target, kept_default_rubric, imported, agents_installed)


def _step_data_directory(console):
    target_str = Prompt.ask(
        "Where should your job-search data live?", default=str(DEFAULT_DATA_DIR)
    )
    target = Path(target_str).expanduser().resolve()
    marker = target / MARKER_DIRNAME

    if marker.is_dir():
        console.print(f"\n{target} is already a jobtracker data directory.")
        reinit = (
            prompt_choice(
                console,
                "Reinitialize it? (resets scaffolded files back to their templates; your "
                ".jobtracker/applications.json is untouched either way)",
                ["No", "Yes"],
                default="No",
            )
            == "Yes"
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
    console.print(
        "[bold]Hard gates[/bold] -- postings that fail any of these get auto-rejected "
        "before scoring.\n"
    )

    gates = []

    if (
        prompt_choice(
            console,
            "Do you have a minimum compensation requirement?",
            ["No", "Yes"],
            default="No",
        )
        == "Yes"
    ):
        amount = IntPrompt.ask(
            "What's the minimum? (just the number, e.g. 150000 or 75)"
        )
        basis = prompt_choice(
            console,
            "Is that an annual salary or an hourly rate?",
            ["annual", "hourly"],
            default="annual",
        )
        if basis == "annual":
            condition = f"base salary disclosed AND < ${amount:,}"
        else:
            condition = f"hourly rate disclosed AND < ${amount:,}/hr"
        gates.append(
            {
                "name": "Compensation floor",
                "condition": condition,
                "reject_message": "Below comp floor",
            }
        )

    if (
        prompt_choice(
            console,
            "\nDo you have a location or remote-work requirement?",
            ["No", "Yes"],
            default="No",
        )
        == "Yes"
    ):
        description = Prompt.ask(
            "Describe it in a sentence (e.g. 'must be fully remote, or onsite/hybrid within "
            "commuting distance of Austin, TX')"
        )
        gates.append(
            {
                "name": "Location",
                "condition": description,
                "reject_message": "Location doesn't work",
            }
        )

    console.print()
    while (
        prompt_choice(
            console,
            "Any other hard requirement that should auto-reject a posting (visa sponsorship, "
            "security clearance, something else)?",
            ["No", "Yes"],
            default="No",
        )
        == "Yes"
    ):
        name = Prompt.ask("Short name for this requirement (e.g. 'Visa sponsorship')")
        condition = Prompt.ask(
            "One-sentence condition that should cause an auto-reject"
        )
        gates.append(
            {
                "name": name,
                "condition": condition,
                "reject_message": f"Fails: {name}",
            }
        )

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
            f"- name: {g['name']}\n"
            f"  condition: {g['condition']}\n"
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

    keep = (
        prompt_choice(
            console,
            "\nKeep these defaults for now?",
            ["Yes", "No"],
            default="Yes",
        )
        == "Yes"
    )
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
            console.print(
                f"[yellow]No file found at {src}. Try again, or press Enter to skip.[/yellow]"
            )
            path_str = Prompt.ask(
                "Enter a file path, or press Enter to skip", default=""
            )
            continue

        imports_dir = target / "resume" / "imports"
        imports_dir.mkdir(parents=True, exist_ok=True)
        dest = imports_dir / src.name
        shutil.copy2(src, dest)
        imported.append(str(dest.relative_to(target)))
        console.print(f"Imported -> {dest.relative_to(target)}")

        if prompt_choice(console, "Add another?", ["No", "Yes"], default="No") != "Yes":
            break
        path_str = Prompt.ask(
            "Enter another file path, or press Enter to skip", default=""
        )

    return imported


_MANUAL_AGENT_TABLE = (
    "\nInstall agents/skills for your coding agent yourself:\n"
    "  Claude Code -- claude plugin marketplace add jpatrickb/jobtracker\n"
    "                 claude plugin install jobtracker@jobtracker-marketplace\n"
    "  Codex       -- .codex/agents/ is auto-discovered, see README's \"Supported Platforms\" table\n"
    "  Kilo Code   -- .kilo/agents/ is auto-discovered, see README's \"Supported Platforms\" table\n"
    "  Cursor      -- /add-plugin jpatrickb/jobtracker (run inside Cursor)\n"
    "  Pi          -- see pi/README.md\n"
    "  Skills (any of the above) -- npx skills add jpatrickb/jobtracker"
)


def _step_agent_install(console, target):
    """Delegates agent+skill installation to the `jobtracker-agents` npx tool (see ../../installer/),
    which lets the user pick which coding agent(s) they use and installs the right files for each.
    Falls back to printing the manual per-platform table on any failure -- missing npx, a network
    error, a nonzero exit, or simply the npm package not being published yet -- since this step is
    optional and should never hard-fail the wizard."""
    npx_bin = shutil.which("npx")
    if not npx_bin:
        console.print(_MANUAL_AGENT_TABLE)
        return False

    console.print("\n[bold]Coding agent setup[/bold]\n")
    if (
        prompt_choice(
            console,
            "Set up your coding agent(s) and skills now?",
            ["Yes", "No"],
            default="Yes",
        )
        != "Yes"
    ):
        console.print("Skipping. Run this yourself whenever you're ready:")
        console.print("  npx jobtracker-agents@latest")
        return False

    try:
        # npx/npm ship as .cmd shims on Windows; subprocess with shell=False won't resolve those
        # the way cmd.exe's own lookup does (see Node's docs on spawning .bat/.cmd files), so route
        # through cmd.exe there instead of calling npx_bin directly.
        if sys.platform == "win32":
            command = ["cmd", "/c", "npx", "--yes", "jobtracker-agents@latest"]
        else:
            command = [npx_bin, "--yes", "jobtracker-agents@latest"]
        # No timeout: unlike the old fast, non-interactive Claude-only shell-outs, this spawns an
        # interactive multiselect session a human is actively driving -- inherited stdio, same as
        # every other subprocess call in this file.
        result = subprocess.run(command, cwd=target)
        if result.returncode != 0:
            raise RuntimeError(f"jobtracker-agents exited {result.returncode}")
    except Exception as exc:
        console.print(f"[yellow]Couldn't run jobtracker-agents ({exc}).[/yellow]")
        console.print(_MANUAL_AGENT_TABLE)
        return False

    return True


def _step_summary(console, target, kept_default_rubric, imported, agents_installed):
    console.print("\n[bold]Summary[/bold]\n")
    console.print(f"  Data directory: {target}")
    console.print(f"  Remembered globally: yes ({config.config_path()})")
    console.print("  Hard gates: see PREFERENCES.md")
    if imported:
        console.print(f"  Imported {len(imported)} file(s): {', '.join(imported)}")
    else:
        console.print("  Resume import: skipped")
    if agents_installed:
        console.print("  Coding agent setup: ran via jobtracker-agents")
    else:
        console.print(
            "  Coding agent setup: not run automatically -- see the commands printed above"
        )

    console.print(
        "\nStill worth knowing about (documented defaults -- edit RUBRIC.md/AGENTS.md directly "
        "to change them):"
    )
    if kept_default_rubric:
        console.print("  - Rubric weights: kept at the scaffolded defaults.")
    console.print("  - Resume length target: 1 page.")
    console.print(
        "  - Cover-letter policy: only written when the employer asks for one, or you do."
    )

    console.print(
        "\n[bold]Next step:[/bold] open your coding agent in this directory and run the "
        "`resume-onboarding` skill to build your evidence ledger"
        + (", using what you imported just now." if imported else ".")
    )
