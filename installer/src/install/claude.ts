import { spawnSync } from "node:child_process";
import { isOnPath } from "../detect.js";
import type { InstallOutcome } from "./types.js";

const REPO = "jpatrickb/jobtracker";
const MARKETPLACE = "jobtracker@jobtracker-marketplace";

const COMMANDS: string[][] = [
  ["plugin", "marketplace", "add", REPO],
  ["plugin", "install", MARKETPLACE],
];

function commandList(): string {
  return COMMANDS.map((args) => `  claude ${args.join(" ")}`).join("\n");
}

export async function installClaude(): Promise<InstallOutcome> {
  if (!isOnPath("claude")) {
    return {
      ok: false,
      message: `\`claude\` not found on PATH. Once Claude Code is installed, run:\n${commandList()}`,
    };
  }

  for (const args of COMMANDS) {
    // Node can't spawn .bat/.cmd shims on Windows without shell:true (the `claude` launcher is
    // one there) -- see https://nodejs.org/api/child_process.html#spawning-bat-and-cmd-files-on-windows.
    const result = spawnSync("claude", args, {
      stdio: "inherit",
      shell: process.platform === "win32",
    });
    if (result.status !== 0) {
      return {
        ok: false,
        message: `\`claude ${args.join(" ")}\` exited ${result.status}. Run these yourself:\n${commandList()}`,
      };
    }
  }

  return { ok: true, message: "Claude Code plugin installed." };
}
