# Rubric

This is the scoring instrument a job-scorer agent applies to every posting, once it has passed
the hard gates in `PREFERENCES.md`.
It is a starting point, not a fixed template.
Add, remove, rename, or reweight dimensions freely until this reflects what actually matters to
you.
The only hard requirement is that the weights across whatever dimensions you keep sum to 100%,
and that the output format section at the bottom stays intact, since the scoring agent and
`jobtracker doctor` both depend on it.

## Dimensions (example weights, sum to 100%)

Each dimension below is scored 0-100 independently, then combined using its weight to produce
the headline score.
Rewrite the "what a strong fit looks like" / "what scores low" guidance in each one to match your
own preferences; the placeholders here are illustrative, not defaults you should keep.

### Compensation (weight: 25%)

What a strong fit looks like: pay meets or exceeds your target range for the role and level.
What scores low: pay is below your target range but still above your hard floor (anything below
the floor should be a hard gate in `PREFERENCES.md`, not a low score here).

### Location / work format (weight: 20%)

What a strong fit looks like: matches your preferred work format (remote / hybrid / onsite) and,
if not fully remote, is within a commute you're actually willing to make.
What scores low: technically workable but a real downgrade from your preference (e.g. hybrid when
you want remote).

### Role fit (weight: 25%)

What a strong fit looks like: the day-to-day responsibilities and required skills line up with
what you actually want to be doing and are good at.
What scores low: the title matches but the substance doesn't (e.g. a "senior engineer" role that's
mostly people-management, when you want to stay hands-on, or vice versa).

### Growth / trajectory (weight: 15%)

What a strong fit looks like: clear room to grow in the direction you want (scope, seniority,
technical depth, or whatever you're optimizing for).
What scores low: a lateral move with no obvious growth path, or growth in a direction you don't
want.

### Culture / team signals (weight: 15%)

What a strong fit looks like: whatever signals in the posting (team structure, values language,
interview process description, size, stage) suggest an environment you'd thrive in.
What scores low: signals that suggest a mismatch (e.g. a pace, structure, or culture you've
specifically learned doesn't work for you).

## Score bands (headline 0 to 100)

| Band | Range | Meaning |
|---|---|---|
| Strong fit | 85-100 | Apply immediately, prioritize over other pending applications |
| Good fit | 70-84 | Apply |
| Worth a look | 50-69 | Apply if time allows, or if something in it stands out |
| Weak fit | 25-49 | Skip unless a specific dimension makes it worth reconsidering |
| Poor fit | 0-24 | Skip |

Adjust these bands and the language for each one to match how you actually want to triage
results.

## Output format

The scoring agent should return, for every posting it scores:

1. **Per-dimension scores**: for each dimension in this rubric, a 0-100 score and a one- to
   two-sentence reason citing what in the posting drove that number.
2. **Weighted total**: the dimension scores combined using the weights above, as a single 0-100
   headline number.
3. **Band**: which row of the score bands table the headline number falls into.
4. **One-line verdict**: a plain-language summary a human can read without opening the full
   scorecard (e.g. "Strong fit: pay and role line up well, hybrid requirement is the only real
   downside.").

This is what gets logged to the tracker via `jobtracker add --score N --band "..."` — see
`AGENTS.md` for how the four pipeline stages fit together (`CLAUDE.md` alongside it is a symlink
to the same file).
