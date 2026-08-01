---
name: resume-onboarding
description: Interviews the user to build their verified work-history ledger from scratch — EVIDENCE.md (what they actually shipped, sourced) and BULLETS.md (resume-ready bullets derived from it). Reads any staged files in resume/imports/ first and drafts candidate entries from them before falling back to a cold interview. Use when a new user's EVIDENCE.md is empty or missing and they want to build it, whenever the user explicitly asks to build or rebuild their evidence ledger, or as a hand-off from the CLI's `jobtracker setup` wizard or from `tailor-application`/`resume-update` when either detects a missing ledger and the user chooses to build it now rather than defer.
tools: Read, Write, Edit, Glob, Grep
---

# Resume Onboarding

Every other file this toolkit ships can start life as a template: a rubric, a preferences file, a
scoring stack, all have a reasonable generic default the user edits from. `EVIDENCE.md` and
`BULLETS.md` can't. A blank evidence ledger is just blank, there's no starter content that means
anything, because the whole point of the ledger is that every line traces back to something the user
actually did. Someone has to ask, and this skill is that interview.

## Before anything else: confirm this is a set-up jobtracker data directory

Check that `resume/` exists (or, more precisely, that `PREFERENCES.md` and `RUBRIC.md` exist in the
current directory — the same marker used elsewhere in this toolkit). If they don't, this isn't a
`jobtracker`-initialized data directory (or you're not in the right one) — tell the user to run
`jobtracker setup` first, then stop there.

## Two ways in

1. **Explicit.** The user asks directly ("build my evidence ledger," "let's do the resume interview,"
   "I haven't set up my resume history yet").
2. **Hand-off.** The CLI's `jobtracker setup` wizard walks a new user through initial configuration and,
   as part of that, may stage imported resume files under `resume/imports/` (see the step below) and
   hand off here to turn them into a real ledger. `tailor-application` or `resume-update` can also find
   `EVIDENCE.md` missing or empty mid-task, offer the user a choice between building it now or deferring,
   and hand off directly here if the user picks now, rather than running its own improvised version of
   this interview. If the user instead picks later, don't run this skill; the calling agent/skill falls
   back to its own narrower, per-application ad hoc question and this ledger just stays unbuilt until the
   user comes back to it.

## What this skill does not build

**`PERSONAL.md`, the non-work personal-connections corpus, is out of scope here, on purpose.**
`PERSONAL.md` answers "why would this person care about this specific company," and that framing has
to come from a real reaction to a real posting, in the moment, in the user's own words. Front-loading
it here would mean guessing at connections before there's a job to connect them to, which is exactly
the kind of inference this toolkit's accuracy rule exists to prevent. `tailor-application` interviews
the user for `PERSONAL.md` per application, ad hoc, when it's actually needed. Don't try to get ahead
of it.

## The non-negotiable rule

No claim, number, or rewrite goes on a resume unless it's traceable to a SHIPPED item in `EVIDENCE.md`,
an actively measured source, or an explicitly labeled, sourced estimate the user has signed off on.
This rule is only as good as the ledger backing it, and for a brand-new user this skill is the entire
ledger's origin. Every entry that goes into `EVIDENCE.md` here gets held to it from the first line, not
loosened because the file is new.

## The three-way taxonomy

Every accomplishment gets exactly one tag. Don't invent a fourth.

- **SHIPPED** — it happened, it's real, and there's a source for it.
- **STARTED-ABANDONED** — real work happened but it didn't ship, or it shipped and then got pulled.
  Worth recording (it can still be true, honest interview material, and sometimes worth a careful
  resume mention), but never worth a number.
- **PLANNED** — intended or in progress, not done yet. Record it so it isn't lost, but it does not
  produce a resume bullet until its status changes to SHIPPED in a later pass.

## Core interview loop

Work role by role, **most recent first**. For each role, ask about accomplishments one at a time
rather than inviting a general narrative, a specific question gets a specific, checkable answer where
an open one gets a summary that's hard to verify:

1. **What did you actually build or ship here?** Ask for the outcome, explicitly not the job
   description. "What did your title involve" produces generic duties language; "what's one thing you
   personally built or changed that existed before you didn't" produces a real accomplishment. If the
   user starts describing responsibilities rather than an outcome, redirect: "sure, but what's a
   specific thing that came out of that?"
2. **How do you know it's true?** Ask for a source directly: a PR or commit link, a metrics dashboard,
   a manager or teammate who'd confirm it, a ticket or launch doc, or "it's my best estimate." Don't
   accept a number without asking where it came from first, the source determines the tag as much as
   the accomplishment does.
3. **Tag it.** SHIPPED if there's a real source behind it. STARTED-ABANDONED if it didn't land.
   PLANNED if it hasn't happened yet. If the user offers a number with no source beyond "I think," that
   is an unverified estimate, not a measured fact, flag it as such rather than tagging it SHIPPED with
   a number attached. It can still be recorded, but only as a labeled estimate pending the user's
   explicit sign-off that it's usable as an estimate on a resume, not as a hard figure.
4. **Get a timeframe.** Even an approximate one ("sometime in 2024," "my last six months there"). A
   ledger entry without a date range is hard to place on a resume timeline later.

Move to the next accomplishment for the same role before moving to the next role. When the user seems
to have run out of things to say about a role, ask once more, narrowly, before moving on: "anything
smaller you're forgetting, something you fixed or built that didn't feel big at the time?" Some of the
most usable bullets are things a user won't volunteer unprompted because they didn't think of them as
an accomplishment.

## Workflow

### 1. Check for staged imports first

Before anything else, check `resume/imports/` (relative to the data directory) for files. This is where
the CLI's `jobtracker setup` wizard (or a user directly) stages a downloaded resume, a LinkedIn export, or
similar, so the interview can start from real content instead of a blank page.

If any files are there:

- Read each one directly (Read handles PDF/docx/text without any conversion step).
- Draft candidate `EVIDENCE.md` entries from what they actually contain: real accomplishments, roles, and
  dates the document states, not generic duties language pulled from a job title.
- Walk the user through the candidates one at a time, the same way step 3 below walks through a cold
  interview answer: confirm each one, correct anything wrong or vague, and tag it (SHIPPED /
  STARTED-ABANDONED / PLANNED, the taxonomy above). An imported resume or LinkedIn export is evidence of
  what the user *claimed* at the time, not a verified source on its own, so still ask where each one
  came from (step 2 of the core interview loop) before tagging anything SHIPPED.
- Once the imported candidates are settled, keep going with the normal interview loop below for whatever
  the imports didn't cover: a role the import barely mentioned, a source none of the imported material
  states, or anything too recent to be in an old document.

If `resume/imports/` is empty or doesn't exist, skip this step entirely and fall back to the cold-interview
flow in the rest of this section, completely unchanged.

### 2. Check what's already there

Read `EVIDENCE.md` and `BULLETS.md` if they exist. If `EVIDENCE.md` already has real entries, don't
restart from zero, ask the user whether this is a fresh build, an update to add a role that's missing,
or a pass to fill in sources for entries that don't have one yet. Don't overwrite existing entries
without the user confirming that's what they want.

### 3. Inventory the roles

Ask for a quick list of roles/positions to cover, most recent first (current or most recent job,
then backward). This is just a skeleton, not the interview itself, don't dig into accomplishments yet.
Confirm the list before starting, so nothing gets skipped because it didn't come to mind unprompted.

### 4. Run the interview loop per role

Apply the core interview loop above to each role in order, most recent first. Keep momentum: cover one
role reasonably completely before moving to the next rather than jumping around, the user's memory of a
given job is more available while they're already thinking about it.

### 5. Write each entry to EVIDENCE.md as it's confirmed

Don't wait until the end of the whole interview to write anything down, if the session gets cut short
partway through, whatever's already confirmed should already be on disk. One entry per accomplishment,
lettered so later files (`BULLETS.md`, and this skill's own future passes) can reference a specific
item unambiguously:

```
### A. <short label for the accomplishment>
- **Status:** SHIPPED | STARTED-ABANDONED | PLANNED
- **When:** <timeframe>
- **Role:** <company / role it happened under>
- **What:** <what actually happened, the user's own account, not a job description>
- **Source:** <PR/commit link, dashboard, named person who'd confirm it, or "estimate, unverified">
- **Numbers:** <any quantified figure and exactly where it came from — omit this line if there isn't one>
```

Continue the letter sequence across the whole file, don't restart it per role. If an entry's number is
an estimate rather than a measured fact, say so explicitly in the Numbers line ("estimate, not
measured") rather than presenting it as a hard figure with the caveat buried in prose.

### 6. Derive BULLETS.md from the SHIPPED entries

Once a role's entries are written, turn its SHIPPED items into resume-ready bullets. Do this per role
as it finishes rather than saving it all for the end, same reasoning as step 5.

- **Only SHIPPED entries become bullets.** STARTED-ABANDONED and PLANNED stay in `EVIDENCE.md` as a
  record but produce nothing in `BULLETS.md` yet, a PLANNED item graduates into a bullet only once a
  later pass moves it to SHIPPED with a real source.
- **Quantify only what the entry's Numbers line actually supports.** If the number is a measured fact,
  use it plainly. If it's a labeled estimate, only include it if the user has explicitly signed off on
  using it that way on a resume, and even then don't present it with more precision than the source
  supports (a rough estimate doesn't become a specific percentage). Never round up, and never add a
  number that isn't in the underlying entry just because the bullet reads better with one.
  - Tag each bullet by skill/theme in brackets (e.g. `[Backend]`, `[AI/LLM]`, `[Leadership]`) so a
    future tailoring pass can pull the right bullets for a given posting without re-reading the whole
    file. Reuse a tag across bullets that share a theme rather than inventing a new one-off tag per
    line.
  - Trace each bullet back to its `EVIDENCE.md` letter, either inline or in a way that's easy to
    cross-reference, so a later accuracy check (this toolkit's non-negotiable rule) has something
    concrete to check the bullet against.

### 7. Confirm what's on disk before ending the session

Summarize what got written: how many roles covered, how many SHIPPED / STARTED-ABANDONED / PLANNED
entries in `EVIDENCE.md`, how many bullets derived into `BULLETS.md`, and which roles (if any) are
still outstanding because the interview ran out of time. Say plainly that `PERSONAL.md` wasn't touched
and why (see above), so the user doesn't assume this pass covered it. If the session is partial, say
what's left so a future run of this skill (or the user directly) knows where to pick back up.
