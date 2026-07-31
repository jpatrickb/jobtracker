# Scoring stack version

This file is the single source of truth for which version of the scoring stack produced any given
score.
Every score logged via `jobtracker add` / `jobtracker rescore` is stamped with the `current_version` value
below, and `jobtracker doctor` warns when a stack input has changed without this file being updated to
match, so a bump nobody remembers to make doesn't silently make old and new scores incomparable
without anything saying so.

current_version: v1

## Scoring stack inputs

These are the files that together determine a score.
Editing any of them can move a posting's score, which is why they're versioned as a group here
rather than individually.

| Input | Path | Notes |
|---|---|---|
| Rubric | `RUBRIC.md` | Dimensions, weights, score bands |
| Preferences | `PREFERENCES.md` | Hard gates and qualitative preferences |
| Anchors | `anchors/` | Worked examples the scorer calibrates against |
| Corrections | `corrections.md` | Accumulated lessons from past scoring disagreements |

The scoring **agent** itself (the prompt/logic that actually reads a posting and applies this
rubric) is not listed here.
It's owned and versioned separately, by whatever plugin or tool you install to do the scoring
(for example, a Claude Code plugin) — this repository only owns the four inputs above.
If a change to the scoring agent itself could move scores, note that in the changelog below by
hand; there's no automated drift check for it the way there is for the four inputs above, since
it doesn't live under this data root.

## Changelog

<!-- One entry per version bump. Record what changed and why, even for a change that turned out
     not to move any scores. -->

### v1

Initial scoring stack. Nothing scored yet.
