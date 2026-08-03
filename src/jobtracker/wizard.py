"""`jobtracker setup`: interactive first-run wizard (see cli.py).

Also what bare `jobtracker` (no subcommand) launches automatically the first time it's run with
no default data directory configured -- see main() in cli.py.

Hard gates, qualitative preferences, the rubric walkthrough, and resume import all used to be
collected here directly. They now live in the `preferences-onboarding` coding-agent skill instead --
a conversational interview handles "what's the least you'd take" ($90k, 110k/yr, whatever the user
actually says) far better than a fixed prompt sequence ever could, and it reaches content this wizard
never touched at all (PREFERENCES.md's qualitative-preferences prose, RUBRIC.md's per-dimension
descriptions). This file's job shrinks to: create the data directory, remember it globally, and hand
off to `jobtracker-agents` for agent/skill installation -- which, on platforms that support it, also
launches straight into a live agent session with that skill already queued up as the first message.
"""

import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt

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
    agents_installed = _step_agent_install(console, target)

    _step_summary(console, target, agents_installed)


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


_MANUAL_AGENT_TABLE = (
    "\nInstall agents/skills for your coding agent yourself:\n"
    "  Claude Code -- claude plugin marketplace add jpatrickb/jobtracker\n"
    "                 claude plugin install jobtracker@jobtracker-marketplace\n"
    "  Codex       -- .codex/agents/ is auto-discovered, see README's \"Supported Platforms\" table\n"
    "  Kilo Code   -- .kilo/agents/ is auto-discovered, see README's \"Supported Platforms\" table\n"
    "  Cursor      -- /add-plugin jpatrickb/jobtracker (run inside Cursor)\n"
    "  Pi          -- see pi/README.md\n"
    "  Skills (any of the above) -- npx skills add jpatrickb/jobtracker\n"
    "\n"
    "Once installed, open your coding agent in this directory and run the "
    "`preferences-onboarding` skill -- hard gates, qualitative preferences, resume import, and "
    "the rubric walkthrough all get set up there now."
)


def _step_agent_install(console, target):
    """Delegates agent+skill installation (and, on Claude Code/Codex, launching straight into a
    live session with `preferences-onboarding` already queued up) to the `jobtracker-agents` npx
    tool (see ../../installer/). Falls back to printing the manual per-platform table on any
    failure -- missing npx, a network error, a nonzero exit, or simply the npm package not being
    published yet -- since this step is optional and should never hard-fail the wizard."""
    npx_bin = shutil.which("npx")
    if not npx_bin:
        console.print(
            "[yellow]`npx` not found -- hard gates, preferences, resume import, and the rubric "
            "walkthrough all live behind a coding-agent skill now, so you'll need Node.js and at "
            "least one coding agent installed to finish setup.[/yellow]"
        )
        console.print(_MANUAL_AGENT_TABLE)
        return False

    console.print("\n[bold]Coding agent setup[/bold]\n")
    if (
        prompt_choice(
            console,
            "Set up your coding agent(s) and skills now? (On Claude Code/Codex, this can drop "
            "you straight into a live session to get started.)",
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
            command = ["cmd", "/c", "npx", "--yes", "jobtracker-agents@latest", "--launch"]
        else:
            command = [npx_bin, "--yes", "jobtracker-agents@latest", "--launch"]
        # No timeout: unlike a fast, non-interactive shell-out, this spawns an interactive
        # multiselect session (and possibly a full agent session afterward) a human is actively
        # driving -- inherited stdio, same as every other subprocess call in this file.
        result = subprocess.run(command, cwd=target)
        if result.returncode != 0:
            raise RuntimeError(f"jobtracker-agents exited {result.returncode}")
    except Exception as exc:
        console.print(f"[yellow]Couldn't run jobtracker-agents ({exc}).[/yellow]")
        console.print(_MANUAL_AGENT_TABLE)
        return False

    return True


def _step_summary(console, target, agents_installed):
    console.print("\n[bold]Summary[/bold]\n")
    console.print(f"  Data directory: {target}")
    console.print(f"  Remembered globally: yes ({config.config_path()})")
    if agents_installed:
        console.print("  Coding agent setup: ran via jobtracker-agents")
    else:
        console.print(
            "  Coding agent setup: not run automatically -- see the commands printed above"
        )

    if agents_installed:
        console.print(
            "\nIf you weren't just dropped into a live agent session above, open your coding "
            "agent in this directory and run the `preferences-onboarding` skill to get started -- "
            "that's where hard gates, preferences, resume import, and the rubric all get set up."
        )
    else:
        console.print(
            "\n[bold]Next step:[/bold] once your coding agent is installed, open it in this "
            "directory and run the `preferences-onboarding` skill to get started."
        )
