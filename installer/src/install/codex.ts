import { fetchAllInto } from "../fetch-file.js";
import { CODEX_AGENT_FILES } from "../manifest.js";
import type { InstallOutcome } from "./types.js";

// Codex auto-discovers project-scoped agents at .codex/agents/ -- no registration step needed.
export async function installCodex(cwd: string, ref: string): Promise<InstallOutcome> {
  try {
    const written = await fetchAllInto(CODEX_AGENT_FILES, `${cwd}/.codex/agents`, ref);
    return {
      ok: true,
      message: `Codex agents installed:\n${written.map((w) => `  ${w}`).join("\n")}`,
    };
  } catch (err) {
    return { ok: false, message: `Couldn't install Codex agents: ${(err as Error).message}` };
  }
}
