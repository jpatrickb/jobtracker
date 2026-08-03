import type { HardGate } from "./hard-gates.js";

// Accepts how people actually type compensation: optional leading $, optional k/m scale suffix,
// optional /yr or /hr unit. "$90k", "110k", "150000", "75/hr", and "90k/yr" all parse.
const COMP_PATTERN = /^\$?\s*([\d,.]+)\s*(k|m)?\s*(\/\s*(hr|hour|yr|year))?$/i;

export function isValidCompFloor(raw: string): boolean {
  return raw.trim() === "" || COMP_PATTERN.test(raw.trim());
}

export function parseCompFloor(raw: string): HardGate | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;
  const match = trimmed.match(COMP_PATTERN);
  if (!match) return null;

  let amount = Number(match[1].replace(/,/g, ""));
  if (!Number.isFinite(amount)) return null;
  const scale = (match[2] ?? "").toLowerCase();
  if (scale === "k") amount *= 1_000;
  if (scale === "m") amount *= 1_000_000;

  const unit = (match[4] ?? "yr").toLowerCase();
  const isHourly = unit.startsWith("h");
  const formatted = amount.toLocaleString("en-US");
  const condition = isHourly
    ? `hourly rate disclosed AND < $${formatted}/hr`
    : `base salary disclosed AND < $${formatted}`;
  return { name: "Compensation floor", condition, rejectMessage: "Below comp floor" };
}
