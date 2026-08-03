#!/usr/bin/env node
// Prototype B -- grouped, fewer prompts, same info collected. Hard gates become one multiselect
// with conditional follow-ups instead of a sequential Y/N-then-detail-then-Y/N-again drill; resume
// import drops the redundant "Add another?" confirm (blank input already means stop, so the extra
// Y/N was never adding information).
import * as p from "@clack/prompts";
import { homedir } from "node:os";
import { join } from "node:path";
import { runAgentInstallStep } from "./lib/agent-step.js";
import { isValidCompFloor, parseCompFloor } from "./lib/comp-floor.js";
import { writeDefaultDataRoot } from "./lib/config.js";
import type { HardGate } from "./lib/hard-gates.js";
import { writeHardGates } from "./lib/hard-gates.js";
import { resolveTarget } from "./lib/paths.js";
import { readRubricDimensions, renderRubricBars } from "./lib/rubric.js";
import { importResumeFile, resolveImportSource } from "./lib/resume-import.js";
import { isJobtrackerDataDir, runScaffold } from "./lib/scaffold.js";

const DEFAULT_DATA_DIR = join(homedir(), "JobTracker");

async function stepDataDirectory(): Promise<string> {
  const targetStr = await p.text({
    message: "Where should your job-search data live?",
    initialValue: DEFAULT_DATA_DIR,
  });
  if (p.isCancel(targetStr)) process.exit(1);
  const target = resolveTarget(targetStr);

  if (isJobtrackerDataDir(target)) {
    const reinit = await p.confirm({
      message: `${target} already exists. Reset it back to a blank starting point? (your tracked applications are safe either way)`,
      initialValue: false,
    });
    if (!p.isCancel(reinit) && reinit) {
      const result = runScaffold(target, true);
      if (result.output) p.log.message(result.output);
      if (!result.ok) {
        p.cancel("`jobtracker init` failed -- is the jobtracker CLI installed and on PATH?");
        process.exit(1);
      }
      p.log.success(`Reinitialized ${target}.`);
    } else {
      p.log.info(`Using ${target} as-is.`);
    }
  } else {
    const result = runScaffold(target, false);
    if (result.output) p.log.message(result.output);
    if (!result.ok) {
      p.cancel("`jobtracker init` failed -- is the jobtracker CLI installed and on PATH?");
      process.exit(1);
    }
    p.log.success(`Created a fresh jobtracker data directory at ${target}.`);
  }

  return target;
}

type GateKind = "comp" | "location" | "visa" | "clearance" | "other";

async function stepHardGates(target: string): Promise<void> {
  const kinds = await p.multiselect({
    message:
      "Let's set up your dealbreakers, so a bad-fit posting gets filtered out automatically. Which of these apply?",
    options: [
      { value: "comp", label: "A minimum pay requirement" },
      { value: "location", label: "A location or remote-work requirement" },
      { value: "visa", label: "Visa sponsorship" },
      { value: "clearance", label: "Security clearance" },
      { value: "other", label: "Something else" },
    ],
    required: false,
  });
  if (p.isCancel(kinds)) return;

  const gates: HardGate[] = [];
  const selected = new Set(kinds as GateKind[]);

  if (selected.has("comp")) {
    const compRaw = await p.text({
      message: "What's the least you'd take? (e.g. $90k, 110k/yr, or 75/hr)",
      validate: (v) => (isValidCompFloor(v ?? "") ? undefined : "e.g. $90k, 110k/yr, or 75/hr"),
    });
    if (!p.isCancel(compRaw)) {
      const gate = parseCompFloor(compRaw);
      if (gate) gates.push(gate);
    }
  }

  if (selected.has("location")) {
    const description = await p.text({
      message: "Where are you willing to work? (e.g. 'remote only', 'Austin or remote')",
    });
    if (!p.isCancel(description)) {
      gates.push({ name: "Location", condition: description, rejectMessage: "Location doesn't work" });
    }
  }

  if (selected.has("visa")) {
    const condition = await p.text({
      message: "One-sentence condition that should auto-reject on visa sponsorship",
      initialValue: "Visa sponsorship not offered AND candidate requires it",
    });
    if (!p.isCancel(condition)) {
      gates.push({ name: "Visa sponsorship", condition, rejectMessage: "Fails: Visa sponsorship" });
    }
  }

  if (selected.has("clearance")) {
    const condition = await p.text({
      message: "One-sentence condition that should auto-reject on security clearance",
      initialValue: "Requires a security clearance the candidate doesn't hold",
    });
    if (!p.isCancel(condition)) {
      gates.push({ name: "Security clearance", condition, rejectMessage: "Fails: Security clearance" });
    }
  }

  if (selected.has("other")) {
    p.log.info("Enter each one as a name, then a blank name to stop.");
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const name = await p.text({ message: "Requirement name (blank to stop)", initialValue: "" });
      if (p.isCancel(name) || !name) break;
      const condition = await p.text({ message: "One-sentence condition that should cause an auto-reject" });
      if (p.isCancel(condition)) break;
      gates.push({ name, condition, rejectMessage: `Fails: ${name}` });
    }
  }

  const wrote = await writeHardGates(target, gates);
  if (gates.length > 0 && wrote) {
    p.log.success(`Wrote ${gates.length} dealbreaker(s) to PREFERENCES.md.`);
  } else {
    p.log.info(
      "No dealbreakers set -- left the illustrative placeholder examples in PREFERENCES.md, edit " +
        "them there whenever you're ready.",
    );
  }
}

async function stepRubricWeights(target: string): Promise<boolean> {
  const dims = await readRubricDimensions(target);
  const summary =
    dims.length > 0 ? renderRubricBars(dims) : "(couldn't find dimension headings in RUBRIC.md to summarize)";
  p.note(summary, "Rubric weights");

  const keep = await p.confirm({
    message: "Does this weighting match what actually matters to you?",
    initialValue: true,
  });
  const kept = !p.isCancel(keep) && keep;
  if (!kept) {
    p.log.info("Edit RUBRIC.md directly whenever you're ready, or revisit it through job-scorer's feedback loop.");
  }
  return kept;
}

async function stepResumeImport(target: string): Promise<string[]> {
  const imported: string[] = [];
  let pathStr = await p.text({
    message:
      "Got a resume or LinkedIn export handy? Drop the path here (or drag the file in) -- blank to skip",
    initialValue: "",
  });
  if (p.isCancel(pathStr)) return imported;

  while (pathStr) {
    const src = resolveImportSource(pathStr);
    if (!src) {
      p.log.warn(`No file found at ${pathStr}.`);
    } else {
      const dest = await importResumeFile(target, src);
      imported.push(dest);
      p.log.success(`Imported -> ${dest}`);
    }
    const next = await p.text({ message: "Another one? (blank to continue)", initialValue: "" });
    if (p.isCancel(next)) break;
    pathStr = next;
  }

  return imported;
}

async function main() {
  p.intro("jobtracker setup (prototype B -- grouped, fewer prompts)");

  const target = await stepDataDirectory();
  const configPath = await writeDefaultDataRoot(target);
  p.log.success(`Remembered ${target} as your default data directory (${configPath}).`);

  await stepHardGates(target);
  const keptDefaultRubric = await stepRubricWeights(target);
  const imported = await stepResumeImport(target);
  await runAgentInstallStep(target);

  p.note(
    [
      `Data directory: ${target}`,
      `Dealbreakers: see PREFERENCES.md`,
      imported.length > 0 ? `Imported ${imported.length} file(s): ${imported.join(", ")}` : "Resume import: skipped",
      keptDefaultRubric ? "Rubric weights: kept at the scaffolded defaults." : "Rubric weights: customize in RUBRIC.md",
    ].join("\n"),
    "Summary",
  );

  p.outro(
    "Next step: open your coding agent in this directory and run the `resume-onboarding` skill " +
      "to build your evidence ledger" +
      (imported.length > 0 ? ", using what you imported just now." : "."),
  );
}

main().catch((err) => {
  p.log.error(err instanceof Error ? err.message : String(err));
  process.exitCode = 1;
});
