// Single source of truth for what gets fetched from the jobtracker repo. If a 4th agent or a 6th
// platform ever shows up, this is the one place that changes -- install/*.ts modules only know
// destinations, not repo-relative source paths.

export const REPO = "jpatrickb/jobtracker";
export const DEFAULT_REF = "main";

export const AGENT_NAMES = ["job-scorer", "resume-reviewer", "tailor-application"] as const;

export const CODEX_AGENT_FILES = AGENT_NAMES.map((name) => `.codex/agents/${name}.toml`);
export const KILO_AGENT_FILES = AGENT_NAMES.map((name) => `.kilo/agents/${name}.md`);
export const PI_AGENT_FILES = AGENT_NAMES.map((name) => `pi/agents/${name}.md`);

// The extension is vendored upstream Pi code (see pi/extensions/subagent/NOTICE.md) -- LICENSE and
// NOTICE.md carry attribution that a symlink-to-a-local-clone preserves implicitly but a network
// fetch doesn't, so they're fetched alongside the two files that are actually loaded at runtime.
export const PI_EXTENSION_FILES = ["index.ts", "agents.ts", "LICENSE", "NOTICE.md"].map(
  (name) => `pi/extensions/subagent/${name}`,
);
