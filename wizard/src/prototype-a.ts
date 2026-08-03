#!/usr/bin/env node
// Prototype A -- direct port. Same exact sequence and content as today's Python wizard
// (src/jobtracker/wizard.py), rebuilt with @clack/prompts primitives one-to-one. This is the
// control: it isolates "was it just the rendering, or was the flow itself annoying" by changing
// only the rendering layer, not the content.
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
    p.log.info(`${target} is already a jobtracker data directory.`);
    const reinit = await p.confirm({
      message:
        "Reset it back to a blank starting point? (your tracked applications are safe either way)",
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

async function stepHardGates(target: string): Promise<void> {
  p.log.step(
    "Let's set up your dealbreakers, so a bad-fit posting gets filtered out automatically " +
      "instead of wasting your time.",
  );

  const gates: HardGate[] = [];

  const compRaw = await p.text({
    message: "What's the least you'd take? (e.g. $90k, 110k/yr, or 75/hr -- blank if you're flexible)",
    initialValue: "",
    validate: (v) => (isValidCompFloor(v ?? "") ? undefined : "e.g. $90k, 110k/yr, or 75/hr"),
  });
  if (!p.isCancel(compRaw)) {
    const gate = parseCompFloor(compRaw);
    if (gate) gates.push(gate);
  }

  const hasLocation = await p.confirm({
    message: "Is there a location or remote-work setup you need?",
    initialValue: false,
  });
  if (!p.isCancel(hasLocation) && hasLocation) {
    const description = await p.text({
      message:
        "Describe it in a sentence (e.g. 'must be fully remote, or onsite/hybrid within " +
        "commuting distance of Austin, TX')",
    });
    if (!p.isCancel(description)) {
      gates.push({ name: "Location", condition: description, rejectMessage: "Location doesn't work" });
    }
  }

  // eslint-disable-next-line no-constant-condition
  while (true) {
    const hasMore = await p.confirm({
      message: "Anything else that should be an automatic no?",
      initialValue: false,
    });
    if (p.isCancel(hasMore) || !hasMore) break;
    const name = await p.text({ message: "Short name for this requirement (e.g. 'Visa sponsorship')" });
    const condition = await p.text({ message: "One-sentence condition that should cause an auto-reject" });
    if (!p.isCancel(name) && !p.isCancel(condition)) {
      gates.push({ name, condition, rejectMessage: `Fails: ${name}` });
    }
  }

  const wrote = await writeHardGates(target, gates);
  if (gates.length > 0 && wrote) {
    p.log.success(`Wrote ${gates.length} dealbreaker(s) to PREFERENCES.md.`);
  } else {
    p.log.info(
      "No dealbreakers set -- left the illustrative placeholder examples in PREFERENCES.md " +
        "(clearly marked as such). Edit them there whenever you're ready.",
    );
  }
}

async function stepRubricWeights(target: string): Promise<boolean> {
  p.log.step("Rubric weights");
  const dims = await readRubricDimensions(target);
  if (dims.length > 0) {
    p.log.message(renderRubricBars(dims));
  } else {
    p.log.warn("(couldn't find dimension headings in RUBRIC.md to summarize)");
  }

  const keep = await p.confirm({
    message: "Does this weighting match what actually matters to you?",
    initialValue: true,
  });
  const kept = !p.isCancel(keep) && keep;
  if (!kept) {
    p.log.info(
      "No problem -- edit RUBRIC.md directly whenever you're ready, or revisit it through " +
        "the job-scorer agent's feedback loop later.",
    );
  }
  return kept;
}

async function stepResumeImport(target: string): Promise<string[]> {
  p.log.step("Got a resume or LinkedIn export handy? Import it now as a starting point, or skip for now.");
  const imported: string[] = [];

  let pathStr = await p.text({
    message: "Drop the file path here (or drag the file in) -- blank to skip",
    initialValue: "",
  });
  if (p.isCancel(pathStr)) return imported;

  while (pathStr) {
    const src = resolveImportSource(pathStr);
    if (!src) {
      p.log.warn(`No file found at ${pathStr}. Try again, or press Enter to skip.`);
      const next = await p.text({ message: "Drop the file path here -- blank to skip", initialValue: "" });
      if (p.isCancel(next)) break;
      pathStr = next;
      continue;
    }

    const dest = await importResumeFile(target, src);
    imported.push(dest);
    p.log.success(`Imported -> ${dest}`);

    const another = await p.confirm({ message: "Got another one to import?", initialValue: false });
    if (p.isCancel(another) || !another) break;
    const next = await p.text({ message: "Drop the next file path here -- blank to skip", initialValue: "" });
    if (p.isCancel(next)) break;
    pathStr = next;
  }

  return imported;
}

async function main() {
  p.intro("jobtracker setup (prototype A -- direct port)");
  p.log.message("Let's get your job-search data directory set up.");

  const target = await stepDataDirectory();
  const configPath = await writeDefaultDataRoot(target);
  p.log.success(
    `Remembered ${target} as your default data directory (${configPath}), so bare \`jobtracker\` works from anywhere now.`,
  );

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
