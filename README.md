# jobtracker

A job-search pipeline that runs on Claude Code: AI agents score postings against *your* own
criteria, tailor a resume and cover letter for each one, and a CLI tracks every application from
first score to final outcome.

It's two things working together:

- **A Claude Code plugin** — agents and skills that do the scoring, tailoring, and review.
- **A CLI (`jobtracker`, or its short alias `jta`)** — a fast, local, JSON-backed record of every
  job you've looked at.

Your own job-search data (scores, applications, resume content, your preferences) never lives
inside this package. It lives in a separate directory you control, ideally your own private git
repo.

## Install

```bash
pip install jobtracker
# or: uv tool install jobtracker
# or: pipx install jobtracker
```

Or, as a convenience wrapper around the same install (picks `uv` if it's on your PATH, otherwise
`pip`, installing `uv` first if you have neither), then launches the setup wizard for you:

```bash
curl -fsSL https://jpatrickb.github.io/jobtracker/install.sh | bash
```

This gives you two equivalent commands, `jobtracker` and `jta`. Examples below use `jobtracker`,
but `jta` works everywhere it does.

Resume and cover-letter PDFs are built with [Typst](https://typst.app/) rather than LaTeX — a
single ~15MB binary instead of a multi-GB TeX distribution:

```bash
brew install typst   # or see https://github.com/typst/typst#installation
```

If you use Claude Code, the setup wizard (below) offers to install the Claude Code plugin for you
automatically. To do it yourself:

```
/plugin marketplace add jpatrickb/jobtracker
/plugin install jobtracker@jobtracker-marketplace
```

## Quickstart

```bash
pip install jobtracker
jobtracker
```

That's the whole flow. Running `jobtracker` with no data directory configured yet launches an
interactive setup wizard (you can also run it explicitly with `jobtracker setup`). It:

- picks or creates a data directory — suggests `~/JobTracker` by default, no manual `mkdir`/`cd`
  needed — and remembers it globally, so `jobtracker` works from anywhere afterward.
- walks through your hard gates (comp floor, location/remote requirement, anything else that
  should auto-reject a posting) and confirms rubric defaults.
- offers to import an existing resume or other proof-of-work document as a starting point — it's
  staged for later use, not auto-parsed.
- offers to wire up the Claude Code plugin automatically, if it finds the `claude` CLI on PATH.

Under the hood, the wizard is a thin layer over `jobtracker init [path]`, a lower-level,
non-interactive command that still exists for anyone who wants manual control — CI, scripting,
power users who'd rather skip the prompts.

## What's inside

**Agents** — dispatch these directly, and run several at once; each runs in its own isolated
context, so they're safe to fire off in bulk (one instance per posting).

| Agent | What it does |
|---|---|
| `job-scorer` | Scores a posting against your rubric and hard gates. Logs every job it scores to the tracker, pass or reject, with the raw listing text. |
| `tailor-application` | Builds a tailored resume (and a cover letter, only if the employer asks for one) for a specific posting, drawing from your own verified accomplishment ledger. Ends with an explicit **NEEDS REVIEW** flag — dispatching `resume-reviewer` against its output is a required manual follow-up, not automatic, now that tailoring runs in its own isolated context. |
| `resume-reviewer` | An independent second pass on any resume or cover letter draft — accuracy, quantification, repetition, ATS fit, length, tone, formatting. |

**Skills** — conversational, run inline in your main session; not meant for bulk dispatch.

| Skill | What it does |
|---|---|
| `resume-update` | General master-resume maintenance, not tied to one posting. |
| `resume-onboarding` | A one-time interview that builds your verified accomplishment ledger — `EVIDENCE.md` and `BULLETS.md` — from scratch, or from an imported resume. |
| `submit-application` | Pre-submit checklist (consistency check, no leftover TODOs, review actually happened), then the human-confirmation gate — the tracker only ever records a job as `Applied` once you confirm you actually submitted it. Deliberately not a bulk operation: real submission happens one job at a time in a browser and needs a human to confirm it. |

## The non-negotiable rule

No claim, number, or rewrite goes on a resume or cover letter unless it's traceable to a verified
("shipped") item in your own evidence ledger, an actively measured source, or an explicitly
labeled, sourced estimate you've signed off on yourself. Every agent and skill in this plugin
defers to that rule.

## Your data directory, after setup

```
~/JobTracker/
├── .jobtracker/             # machine state — the applications.json database, the write lock
├── RUBRIC.md                # scoring dimensions and weights — yours to edit
├── PREFERENCES.md           # hard gates + qualitative preferences — yours to edit
├── SCORING.md                # versions the scoring stack (rubric+preferences+anchors+corrections)
├── corrections.md             # accumulated lessons from past scoring disagreements
├── anchors/                     # real jobs you've scored yourself, used to calibrate the agent
├── listings/                     # raw posting text + extracted facts, one file per job
├── inbox/                          # postings dropped as a file, waiting to be scored
├── applications/                     # one folder per tailored application
├── resume/                            # EVIDENCE.md, BULLETS.md, and (optionally) PERSONAL.md, VOICE.md
│   └── imports/                        # resumes/documents staged during setup, not auto-parsed
├── AGENTS.md                            # the map for a coding-agent session started here
└── CLAUDE.md -> AGENTS.md                # symlink, so Claude Code reads the same file
```

`VOICE.md` (a short description of how you write, so drafts sound like you) is optional — every
agent and skill checks for it and falls back to a general professional tone if it's absent.

## Customizing beyond the wizard

A few defaults are deliberately just documented conventions rather than config options, to keep
the setup wizard short — edit these directly if you want something different:

- **Resume length target** (default: 2 pages) — stated in the reviewer's instructions.
- **Cover-letter policy** (default: only written when the employer asks for one, or you do) —
  stated in `tailor-application`'s instructions.
- **Application status lifecycle** (`Scored → Tailored → Applied → Screening → Interviewing →
  Offer / Rejected / Withdrawn / Skipped`) — a constant in the CLI's source. If your search has a
  meaningfully different shape, edit it there directly.
- **Scoring agent's model** — set via `model:` in `job-scorer`'s frontmatter after installing the
  plugin.

## Other coding agents

`jobtracker` is built for Claude Code today. Support for other coding agents (Codex, Cursor, and
others) is planned, which is why the data directory's instructions file is `AGENTS.md` — an
agent-agnostic convention several tools are converging on — rather than something
Claude-specific. `CLAUDE.md` is just a symlink to it, so Claude Code (which specifically looks for
that filename) reads the exact same content with zero duplication.

### Skills on other agents

The three skills in `skills/` (`resume-update`, `resume-onboarding`, `submit-application`) are
plain [Agent Skills](https://agentskills.io) — a `SKILL.md` with YAML frontmatter plus Markdown
instructions, no Claude-specific mechanism required to follow them. You can install them into any
skills-compatible agent with the community [`vercel-labs/skills`](https://github.com/vercel-labs/skills)
CLI, without waiting on a native plugin port:

```bash
npx skills add jpatrickb/jobtracker
```

This drops the three `SKILL.md` files into whichever agent(s) it detects (or pass `-a <agent>` to
target one directly, `--copy` to write real copies to every requested agent's own skills directory
in one pass instead of relying on symlinks). The three agents (`job-scorer`, `resume-reviewer`,
`tailor-application`) still require the actual Claude Code plugin, since agent dispatch (running an
isolated subagent, not just following written instructions) isn't part of the portable skills
format.

## License

MIT
