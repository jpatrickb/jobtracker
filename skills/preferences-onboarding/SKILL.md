---
name: preferences-onboarding
description: Interviews the user to set up PREFERENCES.md (hard gates that auto-reject a posting, plus the qualitative preferences the rubric scores against) and walks them through RUBRIC.md's dimensions, then hands off to resume-onboarding for the evidence ledger. Use when a new user's PREFERENCES.md still has its placeholder hard gates and blank qualitative-preferences comments, whenever the user explicitly asks to set up or revisit their scoring preferences, or as a hand-off from the CLI's `jobtracker setup` wizard right after it creates the data directory.
tools: Read, Write, Edit, Glob, Grep
---

# Preferences Onboarding

`jobtracker setup` creates `PREFERENCES.md` and `RUBRIC.md` from generic templates — real starting
points, but generic ones. Neither file does anything useful until it reflects this specific user's
actual dealbreakers and what they're actually optimizing for. Someone has to ask, and this skill is
that interview, run inline so a "what's the least you'd take" question can get "$90k, though I'd
flex for the right on-site team" as an answer instead of forcing it through a rigid amount-then-unit
form.

## Before anything else: confirm this is a set-up jobtracker data directory

Check that `PREFERENCES.md` and `RUBRIC.md` exist in the current directory. If they don't, this isn't
a `jobtracker`-initialized data directory (or you're not in the right one) — tell the user to run
`jobtracker setup` first, then stop there.

## Two ways in

1. **Explicit.** The user asks directly ("let's set up my preferences," "I want to change my hard
   gates," "walk me through the rubric").
2. **Hand-off.** The CLI's `jobtracker setup` wizard creates the data directory, installs agents/
   skills for whichever coding agent(s) the user picked, and — on platforms that support it — launches
   straight into a live session with this skill already queued up as the first message. If you're
   reading this because you were just launched that way, there's no separate confirmation step needed;
   just start the interview below.

## Workflow

### 1. Check what's already there

Read `PREFERENCES.md`. If its `## Hard gates` section no longer has the `<!-- No hard gates were set
during jobtracker setup... -->` placeholder comment, real gates already exist — ask whether this is a
fresh setup, an update, or a review, and don't overwrite existing entries without the user confirming
that's what they want. Same check for the `## Qualitative preferences` section's three sub-questions:
if their HTML-comment placeholders are gone, real answers are already there, don't silently replace
them.

### 2. Hard gates (dealbreakers)

Ask conversationally, not as a checklist — accept however the user phrases it and translate it
yourself rather than asking them to pre-format an answer:

- **Compensation floor.** "What's the least you'd take?" Accept whatever shape they answer in ($90k,
  110k/yr, 75/hr, "honestly I'm flexible") and turn it into a condition a scoring agent can evaluate
  against a posting's text, e.g. `base salary disclosed AND < $90,000` or
  `hourly rate disclosed AND < $75/hr`. Skip entirely if they're flexible — that's not a gate.
- **Location / work format.** "Where are you willing to work?" Same principle: whatever they say
  ("remote only," "Austin or remote," "hybrid within 30 minutes of downtown Denver") becomes one
  condition.
- **Anything else that's an automatic no.** Visa sponsorship, security clearance, industries they rule
  out, a title/seniority mismatch, whatever they bring up. Keep asking "anything else?" until they say
  no, don't stop after one.

For each dealbreaker, you need a short name, a condition phrased so a scoring agent can check it
directly against a posting's text/facts, and a short reject message (what gets logged as the rejection
band). Write them into `PREFERENCES.md`'s `## Hard gates (reject before scoring)` section, replacing
its current body (the placeholder comment + example entries, or whatever was there per step 1) but
keeping the heading itself and the "any posting failing ANY gate..." intro line above the list.
Follow this shape for each entry (matches what a scoring agent already expects to read there):

```
- name: Compensation floor
  condition: base salary disclosed AND < $90,000
  reject_message: "Below comp floor"
```

If the user sets zero gates, leave the section's placeholder content in place rather than writing an
empty list — an empty section reads as "nothing rejects," not "nothing was asked yet."

### 3. Qualitative preferences

`PREFERENCES.md`'s `## Qualitative preferences` section has three questions the rubric dimensions
score against. Ask each one, in plain conversational language, and let the user skip any of them:

- What does a strong fit look like for you? Push for specifics (technologies, team structure, problem
  domain, company stage) — "a good team" produces a generic, low-value answer; "a small team doing
  greenfield backend work at a Series B" produces a useful one.
- What should score low, even if it isn't a hard gate? Patterns that clear the hard gates but that
  experience has taught them don't work out.
- Anything else the scorer should know? Industries they're drawn to or trying to break into,
  constraints from their current situation, standing exceptions.

Replace each question's HTML-comment placeholder with the user's actual answer (real prose, not a
summary so compressed it loses the specifics). If they skip a question, leave that one's placeholder
comment in place rather than writing something generic just to fill the space.

### 4. Rubric walkthrough

Read `RUBRIC.md`'s dimensions (name, weight, "what a strong fit looks like" / "what scores low" for
each). Summarize them briefly, then ask one question: does this weighting and description match what
actually matters to them, or do they want to adjust it now? Keeping the defaults is a completely
normal outcome — say so plainly rather than pushing them to customize.

If they want to adjust: dimensions can be renamed, reweighted, added, or removed freely, and each
dimension's "what a strong fit looks like" / "what scores low" prose can be rewritten to match
whatever the user just told you in step 3 (a strong-fit description that mentions greenfield backend
work at a small team, say, should show up in that dimension's prose, not just live in
`PREFERENCES.md`). The one hard requirement: **whatever weights remain must sum to exactly 100.** Do
that arithmetic yourself and don't write the result until it checks out — nothing downstream validates
this for you. Leave the `## Score bands` and `## Output format` sections untouched; they aren't part
of this interview.

If the user would rather defer this and move on to their evidence ledger, that's a legitimate choice —
offer it explicitly rather than assuming everyone wants to go deep on rubric tuning during a first
session. RUBRIC.md stays fully usable at its shipped defaults either way.

### 5. Hand off to resume-onboarding

Once hard gates and qualitative preferences are settled (rubric adjustment is optional, per step 4),
hand off to the `resume-onboarding` skill to build the evidence ledger. Don't try to run an improvised
version of that interview yourself.

### 6. Confirm what's on disk before ending

Summarize what got written: how many hard gates, whether all three qualitative questions were
answered or some were skipped, and whether the rubric was kept as-is or adjusted (and how). If the
session is partial, say plainly what's left so a future run of this skill knows where to pick back up.
