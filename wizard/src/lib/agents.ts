// Thin wrapper calling straight into jobtracker-agents's exported install functions --
// in-process, not a spawned `npx jobtracker-agents` subprocess, so the agent-install phase feels
// like a continuation of this same flow rather than a visible hand-off to a second CLI.
import {
  detectAgents,
  installClaude,
  installCodex,
  installCursor,
  installKilo,
  installPi,
  type InstallOutcome,
  type PiScope,
} from "jobtracker-agents";

export type PlatformId = "claude" | "codex" | "kilo" | "cursor" | "pi";

export const PLATFORM_LABELS: Record<PlatformId, string> = {
  claude: "Claude Code",
  codex: "Codex",
  kilo: "Kilo Code",
  cursor: "Cursor",
  pi: "Pi",
};

export { detectAgents };

export async function installPlatform(
  id: PlatformId,
  target: string,
  ref: string,
  piScope: PiScope,
): Promise<InstallOutcome> {
  switch (id) {
    case "claude":
      return installClaude();
    case "codex":
      return installCodex(target, ref);
    case "kilo":
      return installKilo(target, ref);
    case "cursor":
      return installCursor();
    case "pi":
      return installPi(target, ref, piScope);
  }
}
