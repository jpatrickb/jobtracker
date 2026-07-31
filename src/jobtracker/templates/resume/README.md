# resume/

Your resume source material: the ground truth that every tailored application in `applications/`
draws from, and the accuracy backstop for every claim that goes out under your name.

A reasonable structure to build here over time (none of this is required up front — `jobtracker init`
leaves this directory otherwise empty, and it's fine to grow it gradually):

- **An evidence ledger** — verified accomplishments, each one traceable to something that
  actually shipped or actually happened, distinct from things you started but didn't finish or
  merely planned. This is the backstop referenced in `AGENTS.md`'s "non-negotiable" section
  (`CLAUDE.md` is a symlink to that same file): no claim on a resume or cover letter should go out
  unless it traces back to an entry here.
- **A bullets library** — tagged, resume-ready bullets built from the evidence ledger, so tailored
  resumes can pull pre-written, pre-verified material instead of improvising language (and
  potentially overclaiming) under time pressure.
- **A general-purpose resume** — the one you'd hand a recruiter cold, kept to a clean length,
  separate from the per-application resumes that live in `applications/`.
- **Personal context** — relationships, values, and personal connections to specific domains or
  companies, used only when writing a cover letter or answering "why this company" — never as a
  basis for a factual claim.
- **Standing screener answers** — reusable answers to recurring application-portal questions
  ("years of experience with X"), so you're not re-deriving them from scratch every time.
