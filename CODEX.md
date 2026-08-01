# jobtracker on Codex

This repo's 3 agents (`job-scorer`, `resume-reviewer`, `tailor-application`) are ported to
[Codex](https://developers.openai.com/codex)'s native custom-agent format at `.codex/agents/*.toml`.
This document is the Codex-specific counterpart to the plugin section of the main
[README](README.md): what got ported, how it differs from the Claude Code version, and how to
dispatch these agents reliably today.

**Skills are not part of this port.** jobtracker's 3 skills (`resume-update`, `resume-onboarding`,
`submit-application`) are plain [Agent Skills](https://agentskills.io) files and already install
cleanly on Codex via the community [`vercel-labs/skills`](https://github.com/vercel-labs/skills) CLI:

```bash
npx skills add jpatrickb/jobtracker
```

That was verified end-to-end in issue #7. Nothing in this document duplicates it.

## What's here

| Path | What it is |
|---|---|
| `.codex/agents/job-scorer.toml` | Scores a posting against your rubric and hard gates, logs it to the tracker. |
| `.codex/agents/resume-reviewer.toml` | Independent second pass on a resume or cover letter draft. |
| `.codex/agents/tailor-application.toml` | Builds a tailored resume (and cover letter, if asked for) for one posting. |

Codex discovers project-scoped custom agents at `.codex/agents/` automatically (the same directory
this repo already ships them in) -- there's no manifest registration step. `.codex-plugin/plugin.json`
(this repo's Claude Code plugin manifest) has no documented field for bundling agent TOML files, and
its own [schema reference](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/plugin-creator/references/plugin-json-spec.md)
in the `openai/codex` repo says validation rejects undocumented fields, so nothing was added there for
this port. If a future Codex release adds real plugin-level agent bundling, revisit this.

If you'd rather have these as personal (not project-scoped) agents, copy the same files into
`~/.codex/agents/`.

## How "agent" translates from Claude Code to Codex

Claude Code's plugin `agents:` frontmatter (`tools:`, `model:`) doesn't have a 1:1 Codex equivalent,
so a few things were translated rather than copied verbatim:

- **No per-tool allowlist.** Claude Code's `tools: Read, Glob, Grep, Bash` (etc.) lets you say "Bash
  yes, Write/Edit no." Codex only has the coarser `sandbox_mode` (`read-only` / `workspace-write` /
  `danger-full-access`) -- Bash-equivalent shell access implies write capability once you're above
  `read-only`, there's no way to grant shell but forbid writes. Where Claude Code's tool list encoded a
  real boundary Codex's sandbox can't (`resume-reviewer` has no `Write`/`Edit` on Claude Code, but its
  review procedure still runs `typst compile` through Bash, which writes a PDF), that boundary is now a
  stated rule inside the agent's own `developer_instructions` instead: `sandbox_mode = "workspace-write"`
  for all three, and each file says explicitly what it may and may not write.
- **No `WebFetch`.** `job-scorer`'s Claude Code version uses `WebFetch` to retrieve a posting from a
  URL. Codex's built-in `web_search` returns snippets, not full pages, so `job-scorer.toml` instead
  fetches URLs with `curl` through Bash, or through an MCP fetch server if you bind one via that file's
  `mcp_servers` config (recommended if you have one -- `curl` alone won't render JS-heavy job boards).
- **No model ID pinned for `job-scorer`.** Claude Code's version sets `model: haiku` (its cheapest/
  fastest tier) for bulk-safe dispatch. Codex's model lineup was moving fast enough at the time of this
  port that different current sources disagreed on the exact ID of the current cheapest tier, and
  hardcoding one risked shipping something already retired. `job-scorer.toml` sets
  `model_reasoning_effort = "low"` instead (a stable, non-name-dependent way to ask for a cheaper/faster
  pass) and leaves `model` unset so it inherits your account's configured default. If you want to pin
  a specific small model, check `codex --help` / your account's current model picker and add
  `model = "<id>"` yourself.

## Dispatch: use `codex exec`, not native spawn, for now

Claude Code's Task tool bulk-dispatches these agents (several parallel subagent instances, one per job
posting). Codex's closest native analog is `spawn_agent` calling a named `.codex/agents/*.toml` file --
but as of this port, that path has a family of open upstream regressions where a spawned child ignores
its own TOML config and inherits the parent session's model/instructions instead:
[openai/codex#15250](https://github.com/openai/codex/issues/15250),
[#26868](https://github.com/openai/codex/issues/26868),
[#26408](https://github.com/openai/codex/issues/26408), and related reports. All were still open at
the time of writing.

**The reliable mechanism today is `codex exec`** -- a separate OS process per invocation, not a
spawned child of a running session. It reliably picks up a named agent's own config, supports
`--sandbox` to set the sandbox mode explicitly, and `--json` / `--output-schema` / `-o
<path>`/`--output-last-message <path>` for scripting against its output. This is the direct analog of
Claude Code's bulk Task-tool dispatch: one OS process per job posting or per tailoring task, run
however many you want in parallel.

The `.codex/agents/*.toml` files are still shipped and forward-looking -- once the upstream spawn
regressions are fixed, native in-app dispatch should pick them up with no changes needed here. Until
then, use the patterns below.

### Bulk-score an inbox with `job-scorer`

One `codex exec` process per posting, run however many in parallel your machine/rate limits tolerate:

```bash
cd ~/JobTracker   # your jobtracker data directory
for f in inbox/*; do
  codex exec --sandbox workspace-write \
    -o "/tmp/job-scorer-$(basename "$f").out" \
    "You are running as the job-scorer agent (see .codex/agents/job-scorer.toml in the jobtracker repo
     for full instructions -- load and follow them exactly). Score the posting at $f." &
done
wait
```

(If your Codex version supports named-agent invocation from `codex exec` directly by the time you read
this, prefer that over pasting instructions inline -- check `codex exec --help`.)

### Bulk-tailor several applications

Same shape, one process per job you're tailoring for, each pointed at a specific tracker id or job
description:

```bash
cd ~/JobTracker
for id in 3f9a 7c12 e004; do
  codex exec --sandbox workspace-write \
    -o "/tmp/tailor-$id.out" \
    "You are running as the tailor-application agent (see .codex/agents/tailor-application.toml in the
     jobtracker repo for full instructions -- load and follow them exactly). Build a tailored
     application for tracker id $id." &
done
wait
```

Each run ends its own report with a **NEEDS REVIEW** line, same as the Claude Code version -- collect
those `-o` output files and dispatch `resume-reviewer` (same `codex exec` pattern, one process per
folder that needs review) as the next, separate step.

## Agent vs. skill, restated for Codex

The distinction jobtracker's Claude Code plugin draws between "agent" (independently dispatchable,
safe to bulk-run) and "skill" (conversational, runs inline) carries over to Codex, just expressed
through different mechanisms: an **agent** is a standalone `.codex/agents/*.toml` file with its own
`developer_instructions`/`sandbox_mode`, meant to run as its own `codex exec` process so many instances
can execute independently and in parallel with no shared conversational state; a **skill** is a
`SKILL.md` followed inline in the user's own running session (installed via `npx skills add`), with no
isolated process or parallel-dispatch story of its own -- it's instructions the current session reads
and acts on, not a unit of independent execution.
