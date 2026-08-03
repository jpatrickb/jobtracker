# jobtracker — codebase map for coding agents

This is the map for an agent working on **jobtracker's own source** (this repo). It is not the same
file as `src/jobtracker/templates/AGENTS.md`, which is a *template* — bundled inside the package and
copied into an end user's own separate job-search data directory by `jobtracker setup`/`init`. If
you're here to work on a user's job search, you're in the wrong file; if you're here to fix a bug or
add a feature to jobtracker itself, you're in the right one.

## What this repo is

Two things, sharing one root:

- **A Python CLI** (`src/jobtracker/`) — installable via `pip`/`uv tool install`, gives users the
  `jobtracker`/`jta` commands.
- **A Claude Code plugin** (`.claude-plugin/`, `agents/`, `skills/`) — 3 agents dispatched
  independently/in bulk (`job-scorer`, `resume-reviewer`, `tailor-application`), 3 skills run
  conversationally (`resume-update`, `resume-onboarding`, `submit-application`).

Neither half contains any real user data. All of that (scores, applications, resume content) lives
in a separate directory the *end user* controls, created by `jobtracker init`/`setup` from the
templates bundled at `src/jobtracker/templates/`.

## Layout

| Path | What it is |
|---|---|
| `src/jobtracker/store.py` | Data-root resolution (env var → cwd marker-directory walk-up → global config default), record persistence, id lookup. |
| `src/jobtracker/config.py` | The global `~/.config/jobtracker/config.toml` default-data-root file `jobtracker setup` writes. |
| `src/jobtracker/init.py` | `scaffold()` (shared by `init` and `setup`) — creates a fresh data directory from `templates/`, including the `AGENTS.md`→`CLAUDE.md` symlink. |
| `src/jobtracker/wizard.py` | The interactive `jobtracker setup` wizard. |
| `src/jobtracker/{commands,doctor,facts,listings,scoring,render}.py` | CLI subcommand implementations. |
| `src/jobtracker/templates/` | Bundled, generic starting content for a new data directory (`RUBRIC.md`, `PREFERENCES.md`, `SCORING.md`, `AGENTS.md`, etc.) — package data, shipped inside the wheel. |
| `agents/`, `skills/` | The Claude Code plugin content. Every one of these six files starts with a "confirm this is a set-up jobtracker data directory" guard — don't remove it, it's what stops an agent from improvising when dispatched somewhere `jobtracker setup` hasn't run yet. |
| `resume-templates/` | Typst resume/cover-letter templates `tailor-application` fills in per application. |
| `.claude-plugin/` | `plugin.json` + `marketplace.json` (shared-root pattern — this repo is both the plugin and its own marketplace). |
| `smoke_test.sh` | Before/after behavioral snapshot for the CLI — there's no real test suite yet, this is what CI runs. |
| `installer/` | `jobtracker-agents`, a standalone TypeScript/`@clack/prompts` npm package (invoked via `npx jobtracker-agents`) that lets a user pick which coding agent(s) they use and installs the right agent files (and offers skills) for each. `wizard.py`'s `_step_agent_install` shells out to it, falling back to a manual per-platform table if Node/npx isn't available. |

## Conventions worth knowing before editing

- **The three agents (`job-scorer`, `resume-reviewer`, `tailor-application`) are meant to be
  dispatched independently, possibly several in parallel** (one per job posting). They can't
  self-dispatch another subagent — that's why `tailor-application` ends every run with an explicit
  `**NEEDS REVIEW**` line rather than calling `resume-reviewer` itself. Don't reintroduce a
  self-dispatch assumption into agent-side instructions.
- **The three skills (`resume-update`, `resume-onboarding`, `submit-application`) are conversational**
  and assume they're running inline in the user's own session, not bulk-dispatched.
- **Data-root resolution has three tiers, in order**: `JOBTRACKER_DATA_ROOT`/`JOBTRACKER_DATA_FILE`
  env vars, a `.jobtracker/` marker-directory walk-up from `cwd` (git-style), then the default
  recorded in `~/.config/jobtracker/config.toml`. See `store.find_data_root()`.
- **No claim ships without a source.** The accuracy rule (nothing on a resume/cover letter unless
  traceable to verified work, a measured source, or a labeled, signed-off estimate) is the one rule
  every agent/skill in `agents/`/`skills/` defers to. Don't weaken it when editing those files.
- **This package has never been published under any other name.** If you're touching naming
  (`jobtracker`, the `.jobtracker` marker, `JOBTRACKER_*` env vars, the plugin/marketplace names),
  there's no backward-compatibility burden — grep for the old string and rename it cleanly rather
  than adding a compatibility shim.

## Testing a change

```bash
python3 -m venv .venv && .venv/bin/pip install -e .
JOBTRACKER_BIN=.venv/bin/jobtracker bash smoke_test.sh mytest
claude plugin validate .
```

For a full clean-room test of the actual install experience (not just an editable install), spin up
a bare Linux container (e.g. `docker run -it python:3.13-slim bash`) with nothing pre-installed and
run the install steps straight from README's "Quick Install"/"Manual Setup" sections — that's the
same thing a real user would do, so it's the right test.

## What's not built yet

See open issues on this repo. As of the ports landing, the setup wizard has arrow-key select
menus (with a numbered-list fallback for non-interactive use), and the plugin's 3 dispatchable
agents (`job-scorer`, `resume-reviewer`, `tailor-application`) are ported to Codex (`.codex/`),
Kilo Code (`.kilo/`), Cursor (`.cursor-plugin/`, `cursor-agents/`), and Pi (`pi/`) alongside the
original Claude Code plugin — see README's "Supported platforms" section. The 3 skills are
covered on all of those via `npx skills add jpatrickb/jobtracker` rather than a per-platform port.
Installing agents across all of those platforms is now unified behind `npx jobtracker-agents`
(`installer/`) — pick which agent(s) you use, it installs the right files for each and offers
skills too; `jobtracker setup` runs it automatically when Node is on PATH, falling back to printing
manual per-platform commands otherwise.
Both packages are published: `jobtracker` on PyPI (tag `v<version>` + a GitHub Release triggers
`.github/workflows/publish.yml`) and `jobtracker-agents` on npm (bump `installer/package.json`'s
version and merge to `main` — `.github/workflows/publish-installer.yml` takes it from there, no
manual `npm publish` needed after the first one). Bump `.claude-plugin/plugin.json`, `pyproject.toml`,
and `installer/package.json` together when a change should ship on all fronts at once; nothing
enforces that they stay in lockstep, so don't assume one bump implies the others.
