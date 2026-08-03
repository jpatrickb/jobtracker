// Port of wizard.py's _write_hard_gates/_render_hard_gates_body -- output format matches exactly
// so PREFERENCES.md looks identical regardless of which wizard wrote it.
import { readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";

export interface HardGate {
  name: string;
  condition: string;
  rejectMessage: string;
}

const HEADING = "## Hard gates (reject before scoring)\n";

const INTRO =
  "\nAny posting failing ANY gate below is rejected without being scored.\n" +
  "Keep each gate's `condition` phrased so a scoring agent can evaluate it directly against " +
  "a posting's text/facts, and keep `reject_message` short, it's what gets logged as the " +
  "rejection band.\n\n";

function renderGate(g: HardGate): string {
  return `- name: ${g.name}\n  condition: ${g.condition}\n  reject_message: "${g.rejectMessage}"`;
}

function renderBody(gates: HardGate[]): string {
  if (gates.length > 0) {
    const entries = gates.map(renderGate).join("\n");
    return (
      `${entries}\n\n` +
      "Add, remove, or edit these freely as your requirements change -- this list isn't " +
      "limited to what you entered during `jobtracker setup` (minimum years of experience, " +
      "employment types you won't consider, industries you rule out, company size " +
      "floors/ceilings, and so on all fit here too).\n"
    );
  }
  return (
    "<!-- No hard gates were set during `jobtracker setup`. The two entries below are " +
    "illustrative placeholders, not real defaults -- edit or delete them to match your actual " +
    "requirements. -->\n\n" +
    "- name: Compensation floor\n" +
    "  condition: base salary disclosed AND < $X\n" +
    '  reject_message: "Below comp floor"\n' +
    "- name: Location\n" +
    "  condition: not remote AND not in [your metro]\n" +
    "  reject_message: \"Location doesn't work\"\n\n" +
    "Replace `$X` and `[your metro]` with real values, and add whatever other gates matter to " +
    "you (e.g. minimum years of experience required that you don't meet, employment types you " +
    "won't consider, industries you rule out, company size floors/ceilings, visa sponsorship " +
    "requirements).\n"
  );
}

export async function writeHardGates(target: string, gates: HardGate[]): Promise<boolean> {
  const prefsPath = join(target, "PREFERENCES.md");
  const text = await readFile(prefsPath, "utf8");

  const start = text.indexOf(HEADING);
  if (start === -1) {
    // Heading not found (unexpected custom PREFERENCES.md) -- don't guess, leave it alone.
    return false;
  }

  const nextHeadingIdx = text.indexOf("\n## ", start + HEADING.length);
  const end = nextHeadingIdx !== -1 ? nextHeadingIdx + 1 : text.length;

  const newSection = HEADING + INTRO + renderBody(gates);
  await writeFile(prefsPath, text.slice(0, start) + newSection + text.slice(end), "utf8");
  return true;
}
