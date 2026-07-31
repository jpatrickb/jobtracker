# anchors/

Worked scoring examples the scoring agent calibrates against: real (or realistic) postings paired
with the score you'd actually give them and why.

Anchors exist because a rubric's weights and score bands are abstract until they're pinned down by
concrete examples.
A handful of anchors spanning the range (a clear strong fit, a clear reject, a couple of
genuinely-in-between cases) does more to keep scoring consistent over time than any amount of
extra rubric prose.

## File naming convention

One file per anchor, named for the scenario it captures, e.g.:

```
anchors/strong-fit-remote-senior-swe.md
anchors/reject-comp-below-floor.md
anchors/borderline-hybrid-good-role.md
```

Each file should contain the posting text (or a representative excerpt) plus the score you'd give
it, the band, and a short explanation of the reasoning — written the same way you'd want a
scoring agent's own output to read.
