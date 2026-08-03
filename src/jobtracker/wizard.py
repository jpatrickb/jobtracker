"""`jobtracker setup`: hands off to `jobtracker-agents` (see ../../installer/).

Also what bare `jobtracker` (no subcommand) launches automatically the first time it's run with
no default data directory configured -- see main() in cli.py.

Every interactive step used to live here directly: pick a data directory, hard gates, rubric
weights, resume import, "set up your coding agent(s) now?". All of it has moved -- the data
directory picker into `jobtracker-agents` (a proper `@clack/prompts` flow instead of this file's
plain `rich`/`curses` prompts), and hard gates/preferences/rubric/resume import into the
`preferences-onboarding` coding-agent skill, which a conversational interview suits far better than
a fixed prompt sequence ever could ("what's the least you'd take" gets "$90k, though I'd flex for
the right team" as an answer, not a rigid amount-then-unit form). This file's only job now is the
hand-off itself: find Node, run `jobtracker-agents` unconditionally (no confirmation prompt of its
own), and print manual fallback instructions if Node isn't available.
"""

import shutil
import subprocess
import sys

from rich.console import Console

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
    "Once installed, open your coding agent in a jobtracker data directory (`jobtracker init` "
    "creates one) and run the `preferences-onboarding` skill -- hard gates, qualitative "
    "preferences, resume import, and the rubric walkthrough all get set up there now."
)


def cmd_setup(args=None):
    console = Console(no_color=bool(getattr(args, "plain", False)))

    npx_bin = shutil.which("npx")
    if not npx_bin:
        console.print("[bold]jobtracker setup[/bold]\n")
        if shutil.which("node"):
            # The single most common way to hit this: on Debian/Ubuntu, `nodejs` and `npm` are
            # separate apt packages, so `apt install nodejs` alone doesn't pull in npm/npx -- node
            # being present is not the same as npx being present, and a generic "install Node.js"
            # message doesn't help someone who's already done exactly that.
            console.print(
                "[yellow]Node.js is installed, but `npx` isn't on PATH. On Debian/Ubuntu, "
                "`nodejs` and `npm` are separate packages -- `apt install nodejs` alone doesn't "
                "pull in npm/npx. Install npm too (`apt install npm`), or use nvm or Node's own "
                "installer, which bundle npm/npx with node -- then re-run `jobtracker setup`.[/yellow]"
            )
        else:
            console.print(
                "[yellow]`npx` not found -- picking/creating your data directory, hard gates, "
                "preferences, resume import, and the rubric walkthrough all live behind Node.js and "
                "a coding-agent skill now, so you'll need both installed to finish setup.[/yellow]"
            )
        console.print(_MANUAL_AGENT_TABLE)
        return

    try:
        # npx/npm ship as .cmd shims on Windows; subprocess with shell=False won't resolve those
        # the way cmd.exe's own lookup does (see Node's docs on spawning .bat/.cmd files), so route
        # through cmd.exe there instead of calling npx_bin directly.
        if sys.platform == "win32":
            command = ["cmd", "/c", "npx", "--yes", "jobtracker-agents@latest", "--launch"]
        else:
            command = [npx_bin, "--yes", "jobtracker-agents@latest", "--launch"]
        # No timeout, no cwd: jobtracker-agents now owns picking/creating the data directory
        # itself (including `cd`-ing into it internally) and, on Claude Code/Codex, launching a
        # full interactive agent session afterward -- inherited stdio throughout, same as every
        # other subprocess call in this file used to be.
        result = subprocess.run(command)
        if result.returncode != 0:
            raise RuntimeError(f"jobtracker-agents exited {result.returncode}")
    except Exception as exc:
        console.print("[bold]jobtracker setup[/bold]\n")
        console.print(f"[yellow]Couldn't run jobtracker-agents ({exc}).[/yellow]")
        console.print(_MANUAL_AGENT_TABLE)
