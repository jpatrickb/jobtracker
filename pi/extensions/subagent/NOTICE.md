# Provenance

`index.ts` and `agents.ts` in this directory are vendored **unmodified** (only a short attribution
header comment was added at the top of each file) from Pi's own official example extension:

- Source: https://github.com/earendil-works/pi (repository formerly known as `badlogic/pi-mono`)
- Path: `packages/coding-agent/examples/extensions/subagent/`
- Commit: `008c76f955ae95b6a15703064cc313fdd7b0fde0` (2026-06-18)
- License: MIT, Copyright (c) 2025 Mario Zechner (full text in `./LICENSE`, copied verbatim from the
  upstream repository root; the example directory carries no separate license file of its own, so the
  repository root license governs it)

## Why this is vendored rather than left as documentation

Pi ships with no built-in subagent/dispatch system at all -- its own README states plainly that Pi
"skips features like sub agents" and expects multi-agent workflows to come from extensions. This
example extension is the de facto reference implementation the Pi maintainers themselves point to for
that pattern: a `subagent` tool that spawns an isolated `pi` subprocess per dispatch (`--mode json -p
--no-session`), with single/parallel (`{tasks: [...]}`, capped at 8 tasks / 4 concurrent)/chain
(`{chain: [...]}`) modes, and agent discovery from Markdown+YAML-frontmatter files. jobtracker's three
agents (`job-scorer`, `resume-reviewer`, `tailor-application`) need exactly this dispatch/isolation
model on Claude Code, so vendoring the reference implementation (rather than re-implementing it from
scratch) is both the simplest path and the one most likely to stay compatible with how Pi itself
evolves the pattern.

## What jobtracker adds on top

Nothing in this directory's code. jobtracker's own contribution is the three agent definitions at
`../agents/*.md` (ported from `agents/*.md` in the repo root, which target Claude Code), which this
vendored extension discovers and dispatches. See `../../README.md` (the "Pi" section of the repo's own
README) for installation instructions.

## Updating this vendored copy

If Pi's upstream example extension changes in a way that matters (a bug fix, a new dispatch mode), pull
the new `index.ts`/`agents.ts` from the path above, re-add the attribution header comment, and bump the
commit hash noted here.
