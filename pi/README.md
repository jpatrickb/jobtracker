# jobtracker on Pi

[Pi](https://pi.dev) ([`@earendil-works/pi-coding-agent`](https://www.npmjs.com/package/@earendil-works/pi-coding-agent),
source at [earendil-works/pi](https://github.com/earendil-works/pi), formerly `badlogic/pi-mono`) is a
minimal terminal coding harness by Earendil Inc. This directory is jobtracker's Pi port of the 3 agents
that ship as a Claude Code plugin from the repo root (`agents/job-scorer.md`, `agents/resume-reviewer.md`,
`agents/tailor-application.md`). The 3 skills (`resume-update`, `resume-onboarding`,
`submit-application`) are **not** ported here — they're plain [Agent Skills](https://agentskills.io),
and `npx skills add jpatrickb/jobtracker` already installs them cleanly into Pi (and other
skills-compatible agents) with no jobtracker-specific work needed. This directory is agents only.

## Why this needs an extension, not just 3 markdown files

Pi has no built-in subagent/dispatch system. Its own docs say plainly that Pi "skips features like sub
agents" and expects multi-agent patterns to come from extensions. So porting these 3 agents requires
two things, not one:

1. **The agent definitions themselves** — `pi/agents/*.md`, translated from the Claude Code
   frontmatter format to Pi's.
2. **A dispatch mechanism** — `pi/extensions/subagent/`, which vendors Pi's own official example
   subagent extension (unmodified aside from an attribution header comment; see
   `pi/extensions/subagent/NOTICE.md` for the exact source commit and license). This registers a
   `subagent` tool that spawns an isolated `pi` subprocess per dispatch, with single (`{agent, task}`),
   parallel (`{tasks: [...]}`, up to 8 tasks / 4 concurrent), and chain (`{chain: [...]}`) modes — which
   maps directly onto "dispatch one `job-scorer` per posting, in bulk" and "dispatch one
   `tailor-application` per job."

Without step 2 installed, the agent markdown files in `pi/agents/` are inert: nothing in Pi will
discover or run them.

## Install

From a clone of this repo (or after `pi install git:github.com/jpatrickb/jobtracker`, which pulls in
the extension via this repo's root `package.json` `"pi"` key):

```bash
# 1. Install the subagent-dispatch extension (global, so it's available everywhere)
mkdir -p ~/.pi/agent/extensions/subagent
ln -sf "$(pwd)/pi/extensions/subagent/index.ts" ~/.pi/agent/extensions/subagent/index.ts
ln -sf "$(pwd)/pi/extensions/subagent/agents.ts" ~/.pi/agent/extensions/subagent/agents.ts

# 2. Install jobtracker's 3 agents (global, so `job-scorer` etc. work from any data directory)
mkdir -p ~/.pi/agent/agents
for f in pi/agents/*.md; do
  ln -sf "$(pwd)/$f" ~/.pi/agent/agents/$(basename "$f")
done
```

(`pi install git:github.com/jpatrickb/jobtracker` alone only installs the extension, per its
`package.json` manifest — Pi's package system has no first-class concept of "agent" resources the way
it does for extensions/skills/prompts/themes, so the agent `.md` files still need the manual symlink
step above. This matches upstream's own installation instructions for its sample agents, which use the
identical manual-symlink pattern — see `pi/extensions/subagent/README` link in `NOTICE.md`.)

Prefer project-local agents instead? Symlink into `.pi/agents/` at the root of your jobtracker data
directory instead of `~/.pi/agent/agents/`, and pass `agentScope: "project"` (or `"both"`) when
dispatching. Pi's interactive mode will prompt for a trust confirmation before running project-local
agents the first time, since they're repo-controlled prompts — see the Security Model section in
`pi/extensions/subagent/NOTICE.md`'s linked upstream README for details. The examples below assume the
simpler global (`~/.pi/agent/agents/`) install, which loads unconditionally.

## Usage

From inside your jobtracker data directory (where `PREFERENCES.md`, `RUBRIC.md`, etc. live):

```
Use job-scorer to score this posting: <paste or URL>

Run 3 job-scorers in parallel, one per posting in inbox/

Use tailor-application to build a resume for job abc123

Use resume-reviewer against applications/acme-senior-swe/
```

The `tailor-application` agent's `tools:` frontmatter deliberately excludes the `subagent` tool, so it
cannot dispatch `resume-reviewer` itself — same as on Claude Code, it always ends its run with an
explicit `**NEEDS REVIEW**` line instead, and dispatching `resume-reviewer` afterward is on whoever (or
whatever) is orchestrating it.

## Known functional gap: no WebFetch equivalent

Pi has no built-in URL-fetch tool (`job-scorer`'s Claude Code version uses `WebFetch`;
`tailor-application` uses it too, for a JD given as a bare URL). Rather than writing a custom
`registerTool()` extension just to fetch and clean up a web page, both ported agents' prompts instead
instruct the model to use the `bash` tool directly: `curl -fsSL "<url>"`, then strip HTML into readable
text if needed (a one-liner using Python's stdlib is suggested in the agent files). This is simpler than
a bespoke fetch tool and needs no extra install step, but it is a real functional narrowing worth
knowing about:

- No JavaScript rendering — a posting that's client-side-rendered (no content in the raw HTML response)
  will not work; the agent will report this rather than silently producing a bad extraction.
- Sites with bot-detection/WAF walls that specifically allow browser-shaped requests may reject a plain
  `curl` request that `WebFetch` would have gotten through.

Both agents are instructed to say plainly when a URL fetch fails or looks unusable, and ask for the
posting to be pasted instead, rather than guessing at content they couldn't actually retrieve.

## Model IDs

`job-scorer` pins `model: claude-haiku-4-5` (translated from Claude Code's semantic `model: haiku`
alias — Pi's `model:` frontmatter field takes a literal model id, not an alias, verified against Pi's
own official example agents as of this port). `resume-reviewer` and `tailor-application` carry no
`model:` override, same as their Claude Code originals, so they inherit whatever model the dispatching
`pi` session is running.
