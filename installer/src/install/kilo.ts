import { fetchAllInto } from "../fetch-file.js";
import { KILO_AGENT_FILES } from "../manifest.js";
import type { InstallOutcome } from "./types.js";

// Kilo Code auto-discovers project-scoped agents at .kilo/agents/ -- no registration step needed.
export async function installKilo(cwd: string, ref: string): Promise<InstallOutcome> {
  try {
    const written = await fetchAllInto(KILO_AGENT_FILES, `${cwd}/.kilo/agents`, ref);
    return {
      ok: true,
      message: `Kilo Code agents installed:\n${written.map((w) => `  ${w}`).join("\n")}`,
    };
  } catch (err) {
    return { ok: false, message: `Couldn't install Kilo Code agents: ${(err as Error).message}` };
  }
}
