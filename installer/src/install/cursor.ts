import type { InstallOutcome } from "./types.js";

// Cursor has a plugin-manifest convention (.cursor-plugin/plugin.json, mirroring Claude Code's
// .claude-plugin/), but no CLI binary -- installing a plugin is a slash command run inside
// Cursor's own chat UI, so there's nothing for a shell script to fetch, write, or spawn here.
export async function installCursor(): Promise<InstallOutcome> {
  return {
    ok: true,
    message:
      "Cursor can't be scripted from outside the editor. Open Cursor in this directory and run:\n" +
      "  /add-plugin jpatrickb/jobtracker",
  };
}
