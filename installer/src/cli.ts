#!/usr/bin/env node
import * as p from "@clack/prompts";
import { spawnSync } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";
import { detectAgents } from "./detect.js";
import { installClaude } from "./install/claude.js";
import { installCodex } from "./install/codex.js";
import { installCursor } from "./install/cursor.js";
import { installKilo } from "./install/kilo.js";
import { installPi, type PiScope } from "./install/pi.js";
import type { InstallOutcome } from "./install/types.js";
import { writeDefaultDataRoot } from "./lib/config.js";
import { resolveTarget } from "./lib/paths.js";
import { isJobtrackerDataDir, runScaffold } from "./lib/scaffold.js";
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

const DEFAULT_DATA_DIR = join(homedir(), "JobTracker");

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

// Runs `jobtracker init`/scaffolding and picks a target directory the same way the old Python
// wizard did -- but as part of this same clack-driven flow, not a separate plain-text prompt
// beforehand. If cwd is already a jobtracker data directory (the "standalone re-run to add another
// agent" case README documents), this is a no-op and that directory is used as-is.
async function ensureDataDirectory(flags: Flags): Promise<string> {
  const startCwd = process.cwd();
  if (isJobtrackerDataDir(startCwd)) {
    return startCwd;
  }

  let target: string;
  if (flags.yes) {
    target = resolveTarget(DEFAULT_DATA_DIR);
  } else {
    const targetStr = await p.text({
      message: "Where should your job-search data live?",
      initialValue: DEFAULT_DATA_DIR,
    });
    if (p.isCancel(targetStr)) {
      p.cancel("Cancelled.");
      process.exit(1);
    }
    target = resolveTarget(targetStr as string);
  }

  // Capture this *before* runScaffold below -- it creates the .jobtracker/ marker as a side
  // effect, so checking isJobtrackerDataDir(target) afterward would always say "already exists"
  // regardless of what was actually true beforehand.
  const alreadyExisted = isJobtrackerDataDir(target);

  let reinit = false;
  if (alreadyExisted && !flags.yes) {
    const reinitChoice = await p.confirm({
      message: `${target} already exists. Reset it back to a blank starting point? (your tracked applications are safe either way)`,
      initialValue: false,
    });
    reinit = !p.isCancel(reinitChoice) && reinitChoice;
  }

  if (alreadyExisted && !reinit) {
    // Nothing to do: `jobtracker init` (without --force) on an already-scaffolded directory just
    // refuses with a nonzero exit -- correct behavior for the CLI, but not something to treat as
    // a failure here. Using it as-is means not calling it at all.
    p.log.success(`Using ${target} as-is.`);
  } else {
    const result = runScaffold(target, reinit);
    if (result.output) p.log.message(result.output);
    if (!result.ok) {
      p.cancel("`jobtracker init` failed -- is the jobtracker CLI installed and on PATH?");
      process.exit(1);
    }
    p.log.success(
      reinit ? `Reinitialized ${target}.` : `Created a fresh jobtracker data directory at ${target}.`,
    );
  }

  const configPath = await writeDefaultDataRoot(target);
  p.log.success(`Remembered ${target} as your default data directory (${configPath}).`);

  process.chdir(target);
  return target;
}

async function main() {
  const flags = parseArgs(process.argv.slice(2));

  p.intro("jobtracker-agents");

  const cwd = await ensureDataDirectory(flags);

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
