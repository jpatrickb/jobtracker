# Job Search Pipeline

This directory is your job-search data root: a self-contained collection of postings, scores,
tailored applications, and a tracker, driven by your coding agent working in this directory.
It runs your job search as four stages.
This file is the quick-start map for picking up work in a fresh session.

This file is named `AGENTS.md` per the open convention so any coding agent that reads that file
can pick up this map. A `CLAUDE.md` symlink pointing at this file sits alongside it, since Claude
Code looks for that name specifically. The `job-scorer`, `resume-reviewer`, and `tailor-application`
agents that drive the scoring/tailoring/review stages are available for Claude Code, Codex, Kilo
Code, Cursor, and Pi — see the jobtracker repo's README for per-agent install steps.

## The four stages

| Stage | What it does |
|---|---|
| 1. Search | Score a posting (pasted text, URL, or file) against `PREFERENCES.md` / `RUBRIC.md`. Logs a "Scored" entry to the tracker plus the raw listing text, pass or reject. |
| 2. Tailor | Build a tailored resume for one posting in `applications/<company>-<role>/`, from your resume material plus the posting. A cover letter is written only when the employer asks for one, or you do. |
| 3. Apply | Pre-submit checklist, then log "Applied" once you confirm you actually submitted. |
| 4. Track | `jobtracker` (CLI). One JSON record per job. `list` / `show <id>` / `update-status <id> <status>` / `activity [date] [--status X]` (status changes on a given day, e.g. `activity today --status Applied`, `activity yesterday`). This is how to answer "what's the status of my search" — always check here rather than guessing. |

## Where to start

- **"Let's look at a job"** / posting pasted or linked -> score it against `RUBRIC.md` /
  `PREFERENCES.md`, then `jobtracker add` the result.
- **A posting was dropped as a file rather than pasted** -> work through `inbox/` (see
  `inbox/README.md`), scoring each one and logging it, same as above.
- **"Let's apply to X"** / ready to tailor -> build a tailored resume in a new
  `applications/<company>-<role>/` folder (needs a job description).
- **About to submit, or just did** -> run through a pre-submit checklist, then
  `jobtracker update-status <id> Applied` once you've actually submitted.
- **"How am I doing," "what's pending," "show me my applications"** -> run `jobtracker list` directly
  (add `--status <X>` to filter). Don't guess at status; the tracker is the source of truth.
- **General resume edit not tied to one job** (new accomplishment, wording pass, etc.) -> edit
  your resume material directly, and keep whatever evidence/bullets files you maintain in sync so
  future tailored resumes can use the new material.

## Ground truth files

- `RUBRIC.md` — the scoring dimensions, weights, and score bands. Yours to edit; nothing here is
  fixed.
- `PREFERENCES.md` — hard gates (reject before scoring) plus the qualitative preferences the
  rubric scores against.
- `SCORING.md` — declares the current version of the scoring stack (rubric + preferences +
  anchors + corrections) and a changelog of what changed at each bump. Bump it whenever a change
  to any of those inputs could move a score. **Scores from different versions are not
  comparable**: `jobtracker report` warns when the set is mixed, and `jobtracker list --stale-score` shows
  which records are behind. Rescore with `jobtracker rescore <id>`, which appends rather than
  overwrites, so the original score survives.
- `corrections.md` — a log of corrections/lessons from past scoring disagreements, read by the
  scoring agent alongside `RUBRIC.md` / `PREFERENCES.md`.
- `.jobtracker/applications.json` — never hand-edit; always go through `jobtracker`. Each record also
  carries `source` (site the listing came from), `listing_file` (pointer to its raw text),
  `facts` (structured pay/location/work-format/years-of-experience/etc. for filtering, only what
  the posting actually discloses), and `scorer_version` + `score_history` (which version of the
  scoring stack produced each score).
- `listings/<id>.md` — the raw posting text + facts frontmatter, saved for every job that gets
  **scored**, pass or reject, one file per tracker id. Never hand-edit; go through `jobtracker`.
- `inbox/` — postings captured but not yet scored. Drain this into `listings/` as you process each
  one; empty/absent here means "everything's been looked at."
- `applications/<company>-<role>/` — what actually gets submitted for a specific job. Built fresh
  per application, not copied from a master resume.
- `anchors/` — worked scoring examples the scoring agent calibrates against.
- `resume/` — your resume source material: verified accomplishments, resume-ready bullets, and
  whatever personal context makes a cover letter or tailored application feel genuine rather than
  generic.

## Changing how scoring works: bump the version, every time

**If you edit any of these files, update `SCORING.md` in the same change:**

`RUBRIC.md` · `PREFERENCES.md` · `anchors/*` · `corrections.md`

Together they are the scoring stack (the scoring agent itself is versioned separately, see
`SCORING.md`).
A score is a measurement, and these files are the instrument, so changing one silently makes every
prior score incomparable to every later one without anything in the data saying so.
That is the failure this rule exists to prevent.

The decision to make, every time:

- **Could this change move a score?** Reweighting a dimension, adding or removing a hard gate,
  adding an anchor, adding a correction, sharpening what counts as a strong fit. Then increment
  `current_version` in `SCORING.md` and add a changelog entry saying what changed and why. Offer
  to rescore existing records (`jobtracker list --stale-score` shows what's behind).
- **Can it genuinely not?** A typo, reformatting, a clarifying comment that changes no judgment.
  Then say so under the current version's changelog entry. Record the decision either way, so
  "nobody bumped" is never ambiguous between "it didn't need one" and "someone forgot."

`jobtracker doctor` reports when a stack file has changed without `SCORING.md` being touched. It's a
backstop, not the rule. Don't rely on it to catch you.

## Non-negotiable across every stage

No claim, number, or rewrite goes on a resume or cover letter unless it's traceable to something
you actually did, actively measured from a real source, or an explicitly labeled, sourced
estimate you've signed off on. Fabricated or exaggerated claims are the single most common way an
otherwise-good application gets sunk in review, so keep whatever evidence ledger you maintain
under `resume/` current and treat it as the backstop for everything else.
