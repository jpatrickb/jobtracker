# Resume Review Rubric

Defines how the `resume-reviewer` agent evaluates a resume (or cover letter).
Edited through approved diffs as you give feedback, the same pattern `RUBRIC.md` uses for job-scoring.
This is a starting point — adjust the dimensions, targets, and language to match how you actually want
your own resume held to account.

---

## The non-negotiable rule

**The reviewer may never present a guess as a fact.**
Every number that reaches the resume is either (a) already verified in `EVIDENCE.md`, (b) measured
live by the reviewer from a real, checkable source, or (c) an explicitly labeled estimate built from
real inputs, shown with its formula, and signed off by you before use. There is no fourth path.
A "plausible-sounding" percentage or dollar figure with no formula and no source behind it is exactly
the failure mode that external resume-scoring tools produce — treat any such tool's feedback as
suspect until independently checked against `EVIDENCE.md`.

---

## How review works

1. Read `EVIDENCE.md` and `BULLETS.md` in full before evaluating anything — they are the ground truth for what can and can't be claimed.
2. Check whether the data directory has a `VOICE.md` file. If present, read it for tone rules; if absent, skip silently and apply general professional tone.
3. Read the target file (`resume/resume.typ` by default, or a path under `applications/<job>/` for a tailored version). If reviewing a tailored resume, also read that folder's job description for the ATS/keyword-fit dimension.
4. Walk every bullet clause by clause and apply the weight test, before scoring anything. A true claim
   still has to earn its place: cut any clause that doesn't teach the reader something the rest of the
   sentence doesn't already say. For every number, work out what actually drove it — if it reflects
   something outside the user's control (traffic that never arrived, a purchased list's quality, an
   internal-only benchmark, an unrelated concurrent change) rather than their own work, that's a
   finding; replace-the-number-with-the-system-they-controlled is the fix, not a caveat. Check whether a
   number needs context a single bullet can't give — if the honest read requires a caveat that won't
   fit, that's a finding too, even though the number is true. Check ownership on anything framed as
   resolved or fixed: how much was automated tooling or someone else's call, versus the user's own work?
   Check scale: does this claim represent sustained work across the role, or a single incident dressed
   up as a bullet? A one-off catch, however sharp, doesn't substantiate a title held for months. This
   pass feeds dimension 2 below and the fix list; it is a substance check, separate from the structural
   and stylistic dimensions that follow it.
5. **Check continuity.** List every dated entry in the file in the order they appear, with start and
   end (or "Present"). Confirm two things: the list is sorted newest-to-oldest by start date (with only
   genuinely irrelevant entries, e.g. unrelated performance/volunteer work, allowed to sit out of date
   order at the very end), and every entry's start lines up with or before the previous entry's end, so
   there's no unaccounted stretch of time. A gap is only acceptable if there's a real, known reason for
   it (a semester as a full-time student, say); an unexplained gap, or one that only exists because a
   role covering that stretch got trimmed for relevance, is a finding, report it prominently. This is a
   gate like accuracy and weight: a resume can pass both of those and still fail here.
6. Score each dimension below 0-10 with a specific, line-referenced justification.
7. For every bullet that's naturally quantifiable but currently isn't, don't stop at flagging it — actively try to close the gap (see "Closing a quantification gap" below) before giving up and handing it to the user.
8. Produce a fix list, each item tagged:
   - **SAFE** — grounded already in EVIDENCE.md/BULLETS.md, apply directly.
   - **VERIFY** — a real number almost certainly exists in a live system the reviewer can't reach directly (a cloud console, an analytics dashboard, an app-store console, etc.); name the exact place to look, mirroring EVIDENCE.md's convention for "candidate metrics to verify."
   - **MEASURE** — the number is derivable right now from something the reviewer *can* reach (a git log, a test run, a file count, a repo's own docs). Go run it and report the actual result, don't just suggest running it.
   - **ESTIMATE** — no live source is practically reachable, but a defensible estimate can be built from facts already in EVIDENCE.md (e.g. known rate x known frequency). Show the formula and every input's source. Label it as an estimate wherever it's mentioned. This requires the user's explicit sign-off before it can appear on a resume as a number, and even once approved it should read as an estimate ("roughly," "an estimated") rather than a bare precise figure.
9. Never present a VERIFY or ESTIMATE item with a number already filled in as if it were confirmed. Show the method, not a guess dressed up as a result.

### Closing a quantification gap

When a bullet lacks a number, work through these in order before giving up:
1. **Check EVIDENCE.md's verification-candidates table first** — many gaps already have a known claimed value and a named verification source; that's a VERIFY, not a MEASURE or ESTIMATE.
2. **Check if it's MEASURE-able from the filesystem right now** — commit counts, test suite results, line/contact/file counts, config values in a repo. If the reviewer has Bash access to the relevant directory, run it and report the real number instead of describing how to.
3. **Check if it's VERIFY-able from a live system** the reviewer has no credentials for. Name the exact screen/report.
4. **Only if 1-3 all come up empty, consider ESTIMATE.** An estimate must be built from at least one real, sourced fact (a rate, a count, a duration already verified elsewhere), state the formula plainly, and flag every assumption. If there isn't even a real fact to anchor an estimate to, say so, don't produce a number.

---

## Dimensions

| # | Dimension | What it checks |
|---|-----------|-----------------|
| 1 | Accuracy & groundedness | Every claim traceable to a SHIPPED item in EVIDENCE.md. Zero tolerance dimension: any unverifiable or fabricated claim caps the overall score at Poor regardless of other dimensions. |
| 2 | Weight & ownership | Every clause teaches the reader something or proves real ownership, not restatement. Every number reflects work the user actually controlled (not ad traffic, list quality, an internal-only benchmark, or a concurrent unrelated change) and would read as strong without context a bullet can't give. Anything framed as resolved/fixed is genuinely their work, not an automated tool's or someone else's call. Every claim is sized to sustained work across the role, not a single incident. A gate alongside dimension 1: a bullet can be fully accurate and still fail this dimension. |
| 3 | Quantification | Share of bullets with a real, verified number. Distinguishes "quantifiable but currently missing a number we could add from EVIDENCE.md" from "not naturally quantifiable" (don't penalize the latter). |
| 4 | Verb & phrase variety | Repeated action verbs (>2 uses), repeated phrases, near-duplicate bullets (e.g. a section subtitle restating the first bullet). |
| 5 | Bullet strength & structure | One idea per bullet; leads with a strong, honest verb; follows action + method/tool + result + scope where a result exists; no vague filler ("helped with," "worked on"); states the capability or system that exists rather than narrating how a bug was found and fixed (that's interview material, not the bullet); and where two bullets describe the same underlying system from different angles, they're merged into one framing rather than left as duplicative restatements. |
| 6 | ATS compatibility | Standard section headers, single-column parseable layout, keyword coverage against the target JD if one is provided (tailored review only). |
| 7 | Length & density | Word count (rendered, not source) against a rough target for career stage — adjust this to your own situation; ~550-750 words is a reasonable starting point for someone early in their career. Flag redundancy across sections, not just raw length. |
| 8 | Voice & tone | Matches `VOICE.md` if one exists; otherwise general professional tone — no filler hype words, no invented approximate numbers. |
| 9 | Visual formatting | Build the PDF (`typst compile`) and check: page count reasonable for the content, no awkward orphaned page breaks, section balance (no section starved while another sprawls). |

No fixed weights combine into a single headline score for this rubric (unlike job-scoring) — dimensions
1 and 2 are gates, not weighted inputs, and continuity (step 5 above) is a third gate reported alongside
them rather than scored 0-10: if any of the three fails, say so plainly rather than producing a
misleadingly high composite number. A resume can pass dimension 1 (it's true) and dimension 2 (it
carries real weight) and still fail continuity (an unexplained gap, or entries out of order). For the
rest, report per-dimension 0-10 and an overall qualitative verdict (Strong / Solid / Needs Work / Poor),
not a blended percentage.

---

## Output format

```
## Resume Review — <file reviewed> (<date>)

**Overall: <Strong / Solid / Needs Work / Poor>**
<1-2 sentence summary>

**Accuracy check:** <PASS, or list of unverifiable/fabricated claims found, with the line and why>

**Weight check:** <PASS, or list of clauses/numbers/claims that are true but don't earn their place,
with the line and why: restatement with no new information, a number driven by something the user
didn't control, a number that needs context a bullet can't give, credit claimed for automated/someone
else's work, or a one-off incident sized as if it were sustained work>

**Continuity check:** <PASS, or the specific gap/ordering problem found: which two entries don't
connect, how many months are unaccounted for, and whether a trimmed-for-relevance role is the cause>

| Dimension | Score | Notes |
|---|---|---|
| Quantification | x/10 | ... |
| Verb & phrase variety | x/10 | ... |
| Bullet strength & structure | x/10 | ... |
| ATS compatibility | x/10 | ... |
| Length & density | x/10 | <word count> words (target ~550-750, adjust to your situation) |
| Voice & tone | x/10 | ... |
| Visual formatting | x/10 | ... |

**Fix list:**
1. [SAFE] <specific fix, with the EVIDENCE.md/BULLETS.md line it's grounded in>
2. [MEASURE] <ran X, got real result Y — here's the fix using it>
3. [VERIFY] <the gap, and exactly where to look for the real number; no guess>
4. [ESTIMATE] <formula, every input's source, resulting estimate, clearly labeled — pending your sign-off>
...
```
