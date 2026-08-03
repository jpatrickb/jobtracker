# jobtracker

**Score job postings, tailor resumes, and track applications with AI agents.** Agents and skills
for the coding agent you already use, paired with a local CLI (`jobtracker`, or `jta`). Your
job-search data — scores, applications, resume content, preferences — lives in its own directory
you control, never inside this package.

## Quick Install

```bash
curl -fsSL https://jpatrickb.github.io/jobtracker/install.sh | bash
```

Installs via `uv` or `pip`, then launches the setup wizard: picks a data directory, walks through
your hard gates and rubric, then offers to run `npx jobtracker-agents` — pick which coding agent(s)
you use and it installs the right files for each, plus your skills, in one step. Not on Node? The
wizard prints the equivalent manual commands instead — see Supported Platforms below.

## Supported Platforms

```bash
npx jobtracker-agents
```

Lets you pick which agent(s) you use (Claude Code, Codex, Kilo Code, Cursor, Pi) and installs the
right files for each, then offers to install skills too. This is what the setup wizard runs for you;
run it yourself anytime to add another agent later, or if you skipped it during setup.

| Platform | Agents | Manual install (if you'd rather not use `npx jobtracker-agents`) |
|---|---|---|
| Claude Code | `agents/` | `/plugin marketplace add jpatrickb/jobtracker` then `/plugin install jobtracker@jobtracker-marketplace` |
| [Codex](CODEX.md) | `.codex/agents/` | auto-discovered |
| Kilo Code | `.kilo/agents/` | auto-discovered |
| Cursor | `cursor-agents/` | `/add-plugin jpatrickb/jobtracker` (run inside Cursor — this one can't be scripted, `jobtracker-agents` just prints it too) |
| [Pi](pi/README.md) | `pi/agents/` | see linked docs |

Skills need no per-platform port — `npx skills add jpatrickb/jobtracker` installs all 3
(`resume-update`, `resume-onboarding`, `submit-application`) on any of the above via
[Agent Skills](https://agentskills.io). `jobtracker-agents` offers to run this for you too.

`AGENTS.md` (not `CLAUDE.md`) is the data directory's instructions file — an agent-agnostic
convention several tools converge on.

## Manual Setup

```bash
pip install jobtracker   # or: uv tool install jobtracker / pipx install jobtracker
jobtracker setup         # or: jobtracker init [path] for a non-interactive equivalent
```

| | |
|---|---|
| PDF builds | [Typst](https://typst.app/) — `brew install typst` |

Then run `npx jobtracker-agents` (or see Supported Platforms above for manual steps).

## What's Inside

**Agents** — dispatch directly, run several in parallel, one instance per posting.

| Agent | What it does |
|---|---|
| `job-scorer` | Scores a posting against your rubric and hard gates, logs it to the tracker. |
| `tailor-application` | Builds a tailored resume + cover letter for one posting. Ends with **NEEDS REVIEW** — dispatch `resume-reviewer` next. |
| `resume-reviewer` | Independent second pass on any resume or cover letter draft. |

**Skills** — conversational, run inline in your session, not for bulk dispatch.

| Skill | What it does |
|---|---|
| `resume-update` | General master-resume maintenance. |
| `resume-onboarding` | One-time interview that builds your evidence ledger (`EVIDENCE.md`, `BULLETS.md`). |
| `submit-application` | Pre-submit checklist, then a human-confirmation gate before marking a job `Applied`. |

## The Rule

No claim, number, or rewrite goes on a resume or cover letter unless it traces to a verified item
in your evidence ledger, a measured value, or a signed-off estimate. Every agent and skill defers
to this.

## Data Directory

```
~/JobTracker/
├── .jobtracker/          # applications.json database
├── RUBRIC.md              # scoring weights
├── PREFERENCES.md         # hard gates + preferences
├── SCORING.md              # scoring-stack version
├── corrections.md           # scoring corrections log
├── anchors/                  # calibration jobs
├── listings/                  # posting text + extracted facts
├── inbox/                      # postings waiting to be scored
├── applications/                # one folder per tailored application
├── resume/                       # EVIDENCE.md, BULLETS.md, VOICE.md (optional)
└── AGENTS.md, CLAUDE.md            # agent instructions (CLAUDE.md is a symlink)
```

## Customizing

| Default | Where |
|---|---|
| Resume length (1 page) | `resume-reviewer`'s instructions |
| Cover-letter policy (only when asked) | `tailor-application`'s instructions |
| Status lifecycle | a constant in the CLI source |
| Scoring model | `model:` in `job-scorer`'s frontmatter |

## License

MIT
