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

// Only platforms with a CLI that reliably launches an interactive session pre-seeded with a first
// message ("<bin> '<prompt>'") count as launch-capable. Cursor/Kilo Code are IDE extensions with no
// CLI launch path at all; Pi's behavior here is unconfirmed as of this writing (conflicting docs,
// plus an open upstream issue -- earendil-works/pi#46 -- suggesting it may not persist
// interactively yet), so it's treated the same as the IDE-only platforms for now.
const LAUNCH_CAPABLE: Partial<Record<PlatformId, string>> = {
  claude: "claude",
  codex: "codex",
};

const ONBOARDING_SEED_PROMPT =
  "Run the preferences-onboarding skill to set up my job-search preferences (dealbreakers, " +
  "qualitative preferences, and a rubric walkthrough).";

interface Flags {
  agents: PlatformId[] | null;
  yes: boolean;
  ref: string;
  skills: boolean | null; // null = ask
  launch: boolean;
}

function parseArgs(argv: string[]): Flags {
  const flags: Flags = { agents: null, yes: false, ref: DEFAULT_REF, skills: null, launch: false };
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
    } else if (arg === "--launch") {
      flags.launch = true;
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

  const installedOk: PlatformId[] = [];
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
      installedOk.push(id);
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
          "Also install jobtracker's 4 skills (resume-update, resume-onboarding, submit-application, " +
          "preferences-onboarding) via `npx skills add`?",
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

  // Gated on --launch (only `jobtracker setup` passes it) AND !flags.yes: a --yes/scripted/CI
  // invocation must never block indefinitely on a live interactive child process as a side effect
  // -- this also protects a returning user running `npx jobtracker-agents` standalone later "to add
  // another agent" (see README) from being unexpectedly dropped into a live agent session.
  if (flags.launch && !flags.yes) {
    const launchable = installedOk.filter((id) => id in LAUNCH_CAPABLE);
    if (launchable.length > 0 && process.platform !== "win32") {
      let chosen: PlatformId = launchable[0];
      if (launchable.length > 1) {
        const pick = await p.select({
          message: "Which one do you want to jump into right now?",
          options: launchable.map((id) => ({ value: id, label: PLATFORM_LABELS[id] })),
          initialValue: launchable[0],
        });
        if (!p.isCancel(pick)) chosen = pick as PlatformId;
      }
      const bin = LAUNCH_CAPABLE[chosen];
      if (bin) {
        p.outro(`Launching ${PLATFORM_LABELS[chosen]}...`);
        // No shell, array-form argv -- the seed prompt reaches the child as one argument regardless
        // of spaces/punctuation, no quoting to get wrong. A nonzero/undefined exit here isn't a
        // failure the way it is for the install/skills spawns above: leaving via Ctrl-C, /quit, or
        // Ctrl-D at the end of a real interactive session is success, not an error to report.
        spawnSync(bin, [ONBOARDING_SEED_PROMPT], { stdio: "inherit", cwd, shell: false });
        return;
      }
    }
  }

  p.outro("Done.");
}

main().catch((err) => {
  p.log.error(err instanceof Error ? err.message : String(err));
  process.exitCode = 1;
});
