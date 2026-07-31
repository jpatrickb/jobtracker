---
name: resume-update
description: Update and maintain the user's resume (resume/resume.typ). Use whenever editing the resume, adding or rewriting bullets, tailoring it for a specific job, or verifying claims. Enforces accuracy, the user's voice, and ATS best practices.
---

# Resume Update

Manage changes to the user's resume so it stays accurate, sounds like them, and survives ATS parsing.
The resume is a Typst document at `resume/resume.typ`, built with `typst compile`.

## The non-negotiable rule: accuracy

A resume can have false claims slip in from inference rather than verification, and once that happens
trust in every other claim on it is compromised.
Never put a claim on the resume that you have not verified against a real source.
For every accomplishment, distinguish three states and only the first is resume-worthy:
- **Shipped / done** (real, verifiable) — resume-worthy.
- **Started then abandoned** — NOT an accomplishment.
- **Planned / not built** — NOT an accomplishment.

`resume/EVIDENCE.md` records specific known traps the user has caught before (claims that felt true but
turned out to be started-then-abandoned, or planned-not-built, or attributed to the wrong author). Read
its header and any flagged items before writing a new claim, and don't reintroduce one of those errors.

When a number or specific is not verified, do not invent it.
Either omit it, or add it as a clearly-marked TODO for the user to confirm.
Surface every uncertain claim to the user for confirmation before it goes in.

## The non-negotiable rule: weight

Being true is necessary but not sufficient. A verified claim still has to earn its place, and every
clause of every bullet gets tested the same way: does it teach the reader something the rest of the
sentence doesn't already say, or does it prove real ownership rather than just following a spec? If a
clause does neither, cut it, and when writing what replaces it, reach for the specific and slightly odd
over the generic and safe, a detail like "swapped curl for wget" is harder to fake and reads as more
credible than "fixed a health-check bug."

Numbers get their own version of this test, because a true number can still mislead. Before a number
goes in, work out what actually drove it: if it reflects something the user didn't control, traffic
that never arrived, a purchased list's quality, an internal-only benchmark, an unrelated change that
happened in the same window, then it isn't measuring their engineering, and it should be replaced with
the system or decision they actually built and controlled, even if the original number was completely
accurate. Separately, ask whether the number would read as strong to someone with zero background on
the project; if the honest story needs a caveat a single bullet has no room to give, cut the number
rather than let a true fact create a false impression.

Ownership needs the same scrutiny before a fix or a resolved item gets claimed: check how much of the
work was automated tooling (a bot-generated dependency bump, for instance) or someone else's call, and
rebuild the claim around whatever part was genuinely theirs, or drop it if none of it was. And size every
claim to the role, not a moment: a title held for months needs sustained engineering behind it, systems
built, architecture decided, hard problems solved over time, not a single sharp catch. However good the
judgment behind a one-off, it's an interview story, not a bullet.

Two more habits fall out of this. First, write the capability or system that exists, not the story of
how it came to exist, a debugging narrative is Problem-Action-Result material for an interview, the
bullet just needs to state what's real now. Second, cut anything whose absence wouldn't be surprising:
if failing to have something would obviously be a problem (an app that failed store review, say), then
having it isn't a differentiator worth a line, it's assumed. And when two bullets describe the same
underlying system from different angles, don't write them as separate accomplishments, present one
system with two angles instead, so the resume never has two clauses re-explaining the same mechanism.

## The non-negotiable rule: continuity

Every version of the resume, tailored or not, needs one continuous timeline from the earliest entry
included all the way to the present, in the right order, with no unexplained gap. Sort every entry
newest to oldest by start date, then read down the full list end to end and confirm each entry's start
lines up with, or before, the previous entry's end. A gap only belongs on the resume if there's a real
reason behind it, a semester as a full-time student with no listed role, for instance, never because
trimming a less-relevant role for space or fit happened to leave a hole where it used to sit.

This means checking before cutting, not after. Before removing any job/experience block for relevance,
check what stretch of the timeline it was covering, especially anything dated "Present." If cutting it
would open a gap nothing else fills, shrink it to a single condensed bullet instead of removing it
outright, don't leave an empty section, and don't leave a hole either. The only standing exception is a
role that's genuinely irrelevant to any professional narrative, performance or hobby work, for instance,
that can be pulled out of strict date order and moved to the very end of the list, but everything else
stays in one unbroken chronological sequence, never split across separate lists (an "Experience"
section and a lower-tier "Additional Experience" section, say) that would each read as internally
correct but jump backward and forward in time when read together top to bottom.

## Where to search to identify and verify claims

The evidence sheet `resume/EVIDENCE.md` is the running record of verified accomplishments and candidate
metrics; read it first and keep it updated.

To find or verify a specific piece of work, ask the user where their own evidence lives, don't assume
any particular tool or path. Common places to check, in roughly the order they tend to be useful:
- A personal work journal or daily log, if the user keeps one.
- A ticket tracker or project-management tool (Jira, Linear, GitHub Issues, etc.) for what shipped and when.
- Git history in the relevant repos: `git -C <repo> log --oneline` and README files for what actually landed.
- Performance review documents or manager 1:1 notes, if the user has access to them and they're relevant.
- Metrics sources specific to the claim (an analytics dashboard, a billing console, an ad platform's
  reporting, a CRM export) when the resume claims a measured outcome.
- For work old enough to predate whatever system the user currently uses to track it, ask them directly;
  they may have older work not captured anywhere searchable.

Whatever the user points you to, treat it the same way as any other source: read it, don't infer from
its existence, and cite exactly what you found.

## Voice

Resume bullets are necessarily more compressed than the user's conversational voice, but keep their
plain, grounded word choice. Check whether the user's data directory has a `VOICE.md` file: if present,
read it in full and apply its specific rules; if absent, skip this silently and default to the general
guidance below rather than blocking or asking the user to create one.

- No em dash in prose. (A resume design may use em-dash separators in job headers as a formatting
  choice; that is formatting, not prose, and is fine.)
- Plain words over hype or jargon. Avoid "leveraged, spearheaded, synergy, utilize." Avoid stacked-hyphen jargon like "multi-tenant, server-side, re-platformed, cost-per-lead"; spell the idea out.
- Never write approximate numbers with "~"; use "about" or "around."
- No internal codenames or proper-noun project names; describe the thing in plain words.

## ATS guidance

The resume should stay ATS-friendly: single column, standard section headings, a real comma-separated skills list, standard serif font.
- Strong but honest action verbs: Built, Designed, Shipped, Automated, Reduced, Launched, Deployed.
- One idea per bullet. Do not cram two unrelated points into one bullet.
- Where a real, verified number exists, use the shape: action verb + method/tool + result (number) + scope.
- Quantify only true numbers. A quantified outcome is the single highest-value addition; chase real metrics from the sources above.
- Tailor keywords per application: pull terms from the target job's requirements section and mirror the true ones.
- Check how any icon fonts or symbols in the template render for older ATS parsers; keep the underlying contact text (email/phone) as plain text regardless, and offer a plain-text contact variant if applying somewhere parser-strict.

## The resume's setup

- Source of truth: `resume/resume.typ`. The compiled `resume.pdf` is git-ignored.
- Build: `typst compile resume.typ resume.pdf` (from the `resume/` directory).
- Match whatever reference formatting the user has established (fonts, header style, page breaks). Preserve that look; check the rendered PDF after edits.
- Tracking: one git repo.

## Workflow

1. Check for a `VOICE.md` file in the user's data directory (see the Voice section above) and read `resume/EVIDENCE.md`.
2. Make the edit in `resume/resume.typ`.
3. Verify every new claim against a source; flag anything unverified for the user rather than asserting it.
4. Build with `typst compile` and visually check the PDF: clean, two pages, page breaks and formatting intact.
5. **Mandatory independent review, every time, no exceptions:** dispatch a fresh subagent (Agent tool,
   `subagent_type: resume-reviewer`) on the edited `resume.typ`. Do not review your own edit in place of
   this, the whole point is a second pass from an agent that didn't write the change. Fix every hard
   finding (accuracy, weight, continuity gates) it raises and rebuild before calling the edit done; style
   findings are a judgment call, but say what was left open if anything. See `tailor-application`'s step
   7b for the fuller version of this rule and why it exists.
6. Commit with a clear message describing what changed and why.
7. For a specific application, tailor keywords from the job description (true ones only).
