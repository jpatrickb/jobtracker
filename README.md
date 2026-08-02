# jobtracker

**Score job postings, tailor resumes, and track applications with AI agents.** A Claude Code
plugin (agents + skills) paired with a local CLI (`jobtracker`, or `jta`). Your job-search data —
scores, applications, resume content, preferences — lives in its own directory you control, never
inside this package.

## Quick Install

```bash
curl -fsSL https://jpatrickb.github.io/jobtracker/install.sh | bash
```

Installs via `uv` or `pip`, then launches the setup wizard: picks a data directory, walks through
your hard gates and rubric, wires up the Claude Code plugin if it finds `claude` on PATH.

## Manual Setup

```bash
pip install jobtracker   # or: uv tool install jobtracker / pipx install jobtracker
jobtracker setup         # or: jobtracker init [path] for a non-interactive equivalent
```

| | |
|---|---|
| PDF builds | [Typst](https://typst.app/) — `brew install typst` |
| Claude Code plugin | `/plugin marketplace add jpatrickb/jobtracker` then `/plugin install jobtracker@jobtracker-marketplace` |
| Skills on other agents | `npx skills add jpatrickb/jobtracker` — installs all 3 skills via [Agent Skills](https://agentskills.io) |

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
| Resume length (2 pages) | `resume-reviewer`'s instructions |
| Cover-letter policy (only when asked) | `tailor-application`'s instructions |
| Status lifecycle | a constant in the CLI source |
| Scoring model | `model:` in `job-scorer`'s frontmatter |

## Supported Platforms

`AGENTS.md` (not `CLAUDE.md`) is the data directory's instructions file — an agent-agnostic
convention several tools converge on.

| Platform | Agents | Install |
|---|---|---|
| Claude Code | `agents/` | see Manual Setup above |
| [Codex](CODEX.md) | `.codex/agents/` | auto-discovered |
| Kilo Code | `.kilo/agents/` | auto-discovered |
| Cursor | `cursor-agents/` | `/add-plugin jpatrickb/jobtracker` |
| [Pi](pi/README.md) | `pi/agents/` | see linked docs |

Skills need no per-platform port — `npx skills add jpatrickb/jobtracker` covers all of the above.

## License

MIT
