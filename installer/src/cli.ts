#!/usr/bin/env node
import * as p from "@clack/prompts";
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { detectAgents } from "./detect.js";
import { installClaude } from "./install/claude.js";
import { installCodex } from "./install/codex.js";
import { installCursor } from "./install/cursor.js";
import { installKilo } from "./install/kilo.js";
import { installPi, type PiScope } from "./install/pi.js";
import type { InstallOutcome } from "./install/types.js";
import { DEFAULT_REF } from "./manifest.js";

type PlatformId = "claude" | "codex" | "kilo" | "cursor" | "pi";

const PLATFORM_LABELS: Record<PlatformId, string> = {
  claude: "Claude Code",
  codex: "Codex",
  kilo: "Kilo Code",
  cursor: "Cursor",
  pi: "Pi",
};
const PLATFORM_IDS = Object.keys(PLATFORM_LABELS) as PlatformId[];

interface Flags {
  agents: PlatformId[] | null;
  yes: boolean;
  ref: string;
  skills: boolean | null; // null = ask
}

function parseArgs(argv: string[]): Flags {
  const flags: Flags = { agents: null, yes: false, ref: DEFAULT_REF, skills: null };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--agent" || arg === "--agents") {
      const value = argv[++i] ?? "";
      flags.agents = value
        .split(",")
        .map((s) => s.trim())
        .filter((id): id is PlatformId => PLATFORM_IDS.includes(id as PlatformId));
    } else if (arg === "--yes" || arg === "-y") {
      flags.yes = true;
    } else if (arg === "--ref") {
      flags.ref = argv[++i] ?? DEFAULT_REF;
    } else if (arg === "--skills") {
      flags.skills = true;
    } else if (arg === "--no-skills") {
      flags.skills = false;
    }
  }
  return flags;
}

function isJobtrackerDataDir(cwd: string): boolean {
  return existsSync(resolve(cwd, ".jobtracker"));
}

function isDetected(id: PlatformId, detected: ReturnType<typeof detectAgents>): boolean {
  switch (id) {
    case "claude":
      return detected.claude;
    case "codex":
      return detected.codex;
    case "pi":
      return detected.pi;
    default:
      // Cursor and Kilo Code are IDE extensions with no CLI binary to detect on PATH.
      return false;
  }
}

async function pickScope(): Promise<PiScope | null> {
  const scopeChoice = await p.select({
    message: "Install Pi agents globally or just for this project?",
    options: [
      { value: "global", label: "Global (~/.pi/agent/) -- available everywhere" },
      { value: "project", label: "Project (.pi/) -- only in this data directory" },
    ],
    initialValue: "global",
  });
  if (p.isCancel(scopeChoice)) return null;
  return scopeChoice as PiScope;
}

async function main() {
  const flags = parseArgs(process.argv.slice(2));
  const cwd = process.cwd();

  p.intro("jobtracker-agents");

  if (!isJobtrackerDataDir(cwd)) {
    const message = `${cwd} doesn't look like a jobtracker data directory (no .jobtracker/ marker) -- project-scoped agent files would land here anyway.`;
    if (flags.yes) {
      p.log.warn(message);
    } else {
      const proceed = await p.confirm({ message: `${message} Continue?`, initialValue: false });
      if (p.isCancel(proceed) || !proceed) {
        p.cancel("Stopped -- cd into your jobtracker data directory and try again.");
        process.exitCode = 1;
        return;
      }
    }
  }

  let selected: PlatformId[];
  if (flags.agents) {
    selected = flags.agents;
  } else {
    const detected = detectAgents();
    const choice = await p.multiselect({
      message: "Which coding agent(s) do you use?",
      options: PLATFORM_IDS.map((id) => ({ value: id, label: PLATFORM_LABELS[id] })),
      initialValues: PLATFORM_IDS.filter((id) => isDetected(id, detected)),
      required: false,
    });
    if (p.isCancel(choice)) {
      p.cancel("Cancelled.");
      process.exitCode = 1;
      return;
    }
    selected = choice as PlatformId[];
  }

  if (selected.length === 0) {
    p.log.info("No coding agent selected -- skipping agent install.");
  }

  for (const id of selected) {
    p.log.step(`Setting up ${PLATFORM_LABELS[id]}...`);
    let outcome: InstallOutcome;
    switch (id) {
      case "claude":
        outcome = await installClaude();
        break;
      case "codex":
        outcome = await installCodex(cwd, flags.ref);
        break;
      case "kilo":
        outcome = await installKilo(cwd, flags.ref);
        break;
      case "cursor":
        outcome = await installCursor();
        break;
      case "pi": {
        const scope = flags.yes ? "global" : await pickScope();
        if (scope === null) {
          p.cancel("Cancelled.");
          process.exitCode = 1;
          return;
        }
        outcome = await installPi(cwd, flags.ref, scope);
        break;
      }
    }
    if (outcome.ok) {
      p.log.success(outcome.message);
    } else {
      p.log.error(outcome.message);
    }
  }

  let installSkills = flags.skills;
  if (installSkills === null) {
    if (flags.yes) {
      installSkills = true;
    } else {
      const choice = await p.confirm({
        message:
          "Also install jobtracker's 3 skills (resume-update, resume-onboarding, submit-application) via `npx skills add`?",
        initialValue: true,
      });
      installSkills = p.isCancel(choice) ? false : choice;
    }
  }

  if (installSkills) {
    p.log.step("Running `npx skills add jpatrickb/jobtracker`...");
    const result = spawnSync("npx", ["--yes", "skills@latest", "add", "jpatrickb/jobtracker"], {
      stdio: "inherit",
      cwd,
      shell: process.platform === "win32",
    });
    if (result.status !== 0) {
      p.log.warn(
        "Skills install didn't finish cleanly. Run it yourself:\n  npx skills add jpatrickb/jobtracker",
      );
    }
  }

  p.outro("Done.");
}

main().catch((err) => {
  p.log.error(err instanceof Error ? err.message : String(err));
  process.exitCode = 1;
});
