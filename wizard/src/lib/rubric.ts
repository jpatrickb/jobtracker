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
