import { readFile } from "node:fs/promises";
import { join } from "node:path";

export interface RubricDimension {
  name: string;
  weight: string;
}

export async function readRubricDimensions(target: string): Promise<RubricDimension[]> {
  const text = await readFile(join(target, "RUBRIC.md"), "utf8");
  const re = /^### (.+?)\s*\(weight: (\d+)%\)/gm;
  const dims: RubricDimension[] = [];
  let match: RegExpExecArray | null;
  while ((match = re.exec(text)) !== null) {
    dims.push({ name: match[1], weight: match[2] });
  }
  return dims;
}

// A flat "Name -- 25%" list makes relative weight hard to compare at a glance; a bar makes it
// visually obvious which dimensions actually dominate the score without doing mental math.
export function renderRubricBars(dims: RubricDimension[], barWidth = 20): string {
  const nameWidth = Math.max(0, ...dims.map((d) => d.name.length));
  return dims
    .map((d) => {
      const pct = Number(d.weight);
      const filled = Math.round((pct / 100) * barWidth);
      const bar = "█".repeat(filled) + "░".repeat(Math.max(barWidth - filled, 0));
      return `${d.name.padEnd(nameWidth)}  ${bar}  ${d.weight}%`;
    })
    .join("\n");
}
