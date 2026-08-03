// Shared by all three prototypes verbatim -- the agent-install phase isn't one of the things this
// round of prototyping varies, so it isn't duplicated three times with slight drift.
import * as p from "@clack/prompts";
import { spawnSync } from "node:child_process";
import { detectAgents, installPlatform, PLATFORM_LABELS, type PlatformId } from "./agents.js";

const PLATFORM_IDS = Object.keys(PLATFORM_LABELS) as PlatformId[];
const DEFAULT_REF = "main";

function isDetected(id: PlatformId, detected: ReturnType<typeof detectAgents>): boolean {
  switch (id) {
    case "claude":
      return detected.claude;
    case "codex":
      return detected.codex;
    case "pi":
      return detected.pi;
    default:
      return false;
  }
}

export async function runAgentInstallStep(target: string): Promise<void> {
  const runNow = await p.confirm({
    message: "jobtracker's agents do the actual scoring/tailoring/tracking work -- set up yours now?",
    initialValue: true,
  });
  if (p.isCancel(runNow) || !runNow) {
    p.log.info("No problem. Run `npx jobtracker-agents` whenever you're ready.");
    return;
  }

  const detected = detectAgents();
  const choice = await p.multiselect({
    message: "Which one(s) do you use?",
    options: PLATFORM_IDS.map((id) => ({ value: id, label: PLATFORM_LABELS[id] })),
    initialValues: PLATFORM_IDS.filter((id) => isDetected(id, detected)),
    required: false,
  });
  if (p.isCancel(choice)) {
    p.log.warn("Cancelled agent setup.");
    return;
  }

  for (const id of choice as PlatformId[]) {
    p.log.step(`Setting up ${PLATFORM_LABELS[id]}...`);
    let piScope: "global" | "project" = "global";
    if (id === "pi") {
      const scopeChoice = await p.select({
        message: "Install Pi agents globally or just for this project?",
        options: [
          { value: "global", label: "Global (~/.pi/agent/) -- available everywhere" },
          { value: "project", label: "Project (.pi/) -- only in this data directory" },
        ],
        initialValue: "global",
      });
      if (p.isCancel(scopeChoice)) continue;
      piScope = scopeChoice as "global" | "project";
    }
    const outcome = await installPlatform(id, target, DEFAULT_REF, piScope);
    if (outcome.ok) p.log.success(outcome.message);
    else p.log.error(outcome.message);
  }

  const installSkills = await p.confirm({
    message: "Also install jobtracker's 3 skills via `npx skills add`?",
    initialValue: true,
  });
  if (!p.isCancel(installSkills) && installSkills) {
    p.log.step("Running `npx skills add jpatrickb/jobtracker`...");
    const result = spawnSync("npx", ["--yes", "skills@latest", "add", "jpatrickb/jobtracker"], {
      stdio: "inherit",
      cwd: target,
      shell: process.platform === "win32",
    });
    if (result.status !== 0) {
      p.log.warn(
        "Skills install didn't finish cleanly. Run it yourself: npx skills add jpatrickb/jobtracker",
      );
    }
  }
}
