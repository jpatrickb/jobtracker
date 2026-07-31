# Preferences

This file has two jobs: declare the hard gates that reject a posting before it's even scored, and
describe the qualitative preferences the dimensions in `RUBRIC.md` score against.
Both sections are meant to be edited freely and kept current as your preferences change or
sharpen.

## Hard gates (reject before scoring)

Any posting failing ANY gate below is rejected without being scored.
This list is open-ended: add, remove, or edit entries freely, it is not limited to the examples
below.
Keep each gate's `condition` phrased so a scoring agent can evaluate it directly against a
posting's text/facts, and keep `reject_message` short, it's what gets logged as the rejection
band.

- name: Compensation floor
  condition: base salary disclosed AND < $X
  reject_message: "Below comp floor"
- name: Location
  condition: not remote AND not in [your metro]
  reject_message: "Location doesn't work"

Replace `$X` and `[your metro]` with real values, and add whatever other gates matter to you
(e.g. minimum years of experience required that you don't meet, employment types you won't
consider, industries you rule out, company size floors/ceilings, visa sponsorship requirements).
A gate with a condition that can never be checked from a posting's own text is not useful here;
if you find yourself writing one, it probably belongs in a rubric dimension instead, scored
low rather than rejected outright.

## Qualitative preferences

The prompts below are what the rubric dimensions in `RUBRIC.md` score against.
Fill them in with real specifics, generic answers produce generic (and therefore not very useful)
scores.

### What does a strong fit look like for you?

<!-- Describe the kind of role, team, company stage, and day-to-day work that would make you
     genuinely excited. Be specific: name technologies, team structures, problem domains,
     company stages, or anything else that's concretely true of your best-fit roles. -->

### What should score low, even if it isn't a hard gate?

<!-- Describe patterns that technically clear your hard gates but that experience has taught you
     tend not to work out. E.g. specific role/title mismatches, culture red flags you've learned
     to spot in a posting's language, team structures that haven't worked for you before. -->

### Anything else the scorer should know?

<!-- Anything that doesn't fit neatly into "strong fit" or "should score low" but still shapes
     how you'd want a posting judged, e.g. industries you're especially drawn to or trying to
     break into, constraints from your current situation, or standing exceptions to the rules
     above. -->
