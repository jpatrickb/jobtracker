// Pure PATH-presence check, same spirit as Python's shutil.which -- deliberately NOT spawning
// `<bin> --version`, since not every binary supports that flag or exits promptly (a hang on stdin
// is a real if unlikely failure mode we don't need to risk just to detect presence).

import { accessSync, constants } from "node:fs";
import { delimiter, join } from "node:path";

function candidateNames(cmd: string): string[] {
  if (process.platform !== "win32") return [cmd];
  const pathext = (process.env.PATHEXT ?? ".COM;.EXE;.BAT;.CMD").split(";");
  return [cmd, ...pathext.map((ext) => cmd + ext.toLowerCase())];
}

export function isOnPath(cmd: string): boolean {
  const dirs = (process.env.PATH ?? "").split(delimiter).filter(Boolean);
  for (const dir of dirs) {
    for (const name of candidateNames(cmd)) {
      try {
        accessSync(join(dir, name), constants.X_OK);
        return true;
      } catch {
        // not here, keep looking
      }
    }
  }
  return false;
}

export interface DetectedAgents {
  claude: boolean;
  codex: boolean;
  pi: boolean;
}

// Cursor and Kilo Code have no CLI binary to detect (they're IDE extensions) -- callers should
// always present them as selectable-but-unchecked options rather than trying to guess.
export function detectAgents(): DetectedAgents {
  return {
    claude: isOnPath("claude"),
    codex: isOnPath("codex"),
    pi: isOnPath("pi"),
  };
}
