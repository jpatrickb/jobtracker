import { homedir } from "node:os";
import { fetchAllInto } from "../fetch-file.js";
import { PI_AGENT_FILES, PI_EXTENSION_FILES } from "../manifest.js";
import type { InstallOutcome } from "./types.js";

export type PiScope = "global" | "project";

// Agents can be global (~/.pi/agent/agents/) or project-local (.pi/agents/), per pi/README.md's
// own documented distinction. The dispatch extension only has a documented *global* install path
// there -- there's no project-scoped extension convention -- so it always installs globally
// regardless of `scope`.
export async function installPi(cwd: string, ref: string, scope: PiScope): Promise<InstallOutcome> {
  const agentsDir = scope === "global" ? `${homedir()}/.pi/agent/agents` : `${cwd}/.pi/agents`;
  const extensionDir = `${homedir()}/.pi/agent/extensions/subagent`;

  try {
    const agentFiles = await fetchAllInto(PI_AGENT_FILES, agentsDir, ref);
    const extensionFiles = await fetchAllInto(PI_EXTENSION_FILES, extensionDir, ref);
    return {
      ok: true,
      message: `Pi agents installed (${scope}):\n${[...agentFiles, ...extensionFiles]
        .map((w) => `  ${w}`)
        .join("\n")}`,
    };
  } catch (err) {
    return { ok: false, message: `Couldn't install Pi agents: ${(err as Error).message}` };
  }
}
