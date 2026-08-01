---
name: submit-application
description: Pre-submission checklist for a tailored application, then logs the Applied status in the tracker once the user confirms they actually submitted it. Use right before or right after submitting a job application through a company's portal.
---

# Submit Application

The last step of the pipeline: Searching (`job-scorer`) -> Tailoring (`tailor-application`,
`resume-reviewer`) -> **Applying** (this skill) -> Tracking (`jobtracker`).

Actual submission happens through each company's own portal, by hand. This skill doesn't and can't
automate that (portals vary, and some ask one-off supplemental questions). What it does is make sure the
application is actually ready, then record that it went out.

## Before anything else: confirm this is a set-up jobtracker data directory

Check that `PREFERENCES.md` and an `applications/` directory exist in the current directory. If not,
this isn't a `jobtracker`-initialized data directory (or you're not in the right one) — tell the user
to run `jobtracker setup` first, then stop there.

## Workflow

1. **Identify the folder.** `applications/<company>-<role-slug>/`. Ask if not given.

2. **Checklist:**
   - `resume.typ`, `resume.pdf`, `cover-letter.typ`, `cover-letter.pdf`, and a `job-description.*` file
     all exist in the folder.
   - **Check whether the tailoring agent flagged anything incomplete.** `tailor-application` now runs as
     an isolated agent, expected to finish in a submission-ready state or say explicitly in its final
     report what it couldn't resolve on its own (a missing personal angle, an ambiguous fact, a
     duplicate-posting question, an unresolved `%%TODO%%`). Read that report rather than independently
     re-scanning the files for loose ends, and resolve whatever it flagged before treating the checklist
     as passed.
   - **`resume-reviewer` must have actually run, and this is a blocking gate, not a question to ask the
     user.** `tailor-application`'s final report ends with an unmissable **NEEDS REVIEW** line whenever
     review is still outstanding, since it can no longer dispatch `resume-reviewer` itself from an
     isolated agent context the way the old skill-based version could. That line still showing (or no
     report to check at all, e.g. an older folder, a resume built outside `tailor-application`, or a
     `.typ` file edited since the last review) means the gate hasn't been cleared yet. The gate exists
     because a resume-reviewer pass is the only check that catches accuracy, weight, and continuity
     problems from a second, independent read: a writer reviewing its own draft shares its blind spots,
     and an application that skips this step can go out with an unverified claim or an unexplained
     employment gap nobody caught. If it's still outstanding, run it now yourself before continuing
     (dispatch `resume-reviewer` as an independent review pass, using however your environment supports
     invoking another agent/skill, one call per file that exists) rather than asking the user whether to
     skip it. Fix every hard finding (accuracy/weight/continuity) it raises before treating the checklist
     as passed. Never take "it looks fine" from the user as a substitute for the review actually running.
   - Rebuild both PDFs if either `.typ` file changed since last build, and confirm they render cleanly.
   - **Run `jobtracker doctor`** and resolve anything it flags for this record before moving on: a missing
     listing file, a `set-folder` link that no longer resolves to a real directory, or facts drift
     between the tracker and what's actually in the folder. This is a consistency check, not a
     formality, catch it here rather than letting a stale link sit in the tracker after the status
     changes to Applied.

3. **Once the checklist passes, ask the user to confirm they actually clicked submit.** Do not assume or
   log "Applied" preemptively, this is a real-world action outside the agent's control, and the whole
   point of the tracker is that it reflects what really happened.

4. **Once confirmed, update the tracker:**
   - Find the id: `jobtracker list --company <company> --json`. Every job scored by `job-scorer` should
     already have a "Scored" entry. Use `jobtracker show <id> --json` if you need to confirm the exact
     current status or facts precisely rather than just show something to the user, `--json` is easier
     to parse reliably than the human-formatted output.
   - If no entry exists (the job was never scored, e.g. the user found it another way), create one first:
     `jobtracker add --company "<Company>" --role "<Role>" --score <N> --band "<band>"`.
     If there's no score at all, ask the user for one rather than inventing a number, or note the gap.
   - Link the folder: `jobtracker set-folder <id> applications/<company>-<role-slug>`
   - Log the submission: `jobtracker update-status <id> Applied --note "<short note>"`

5. **Confirm back** with the tracker id and current status.
