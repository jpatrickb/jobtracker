// Library entry point for consumers that want to call into jobtracker-agents directly (in-process)
// rather than spawning `npx jobtracker-agents` as a subprocess -- e.g. the setup wizard, which
// wants the agent-install phase to feel like a continuation of the same flow, not a visible
// hand-off to a second CLI. The `jobtracker-agents` bin (dist/cli.js) is unaffected by this.

export { detectAgents, isOnPath, type DetectedAgents } from "./detect.js";
export { DEFAULT_REF, REPO } from "./manifest.js";
export { installClaude } from "./install/claude.js";
export { installCodex } from "./install/codex.js";
export { installKilo } from "./install/kilo.js";
export { installCursor } from "./install/cursor.js";
export { installPi, type PiScope } from "./install/pi.js";
export type { InstallOutcome } from "./install/types.js";
