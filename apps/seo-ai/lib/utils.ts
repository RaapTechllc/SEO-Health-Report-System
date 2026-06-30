import type { Grade } from "./types";

/** Map a 0..100 score to a letter grade. */
export function toGrade(score: number): Grade {
  if (score >= 90) return "A";
  if (score >= 80) return "B";
  if (score >= 70) return "C";
  if (score >= 55) return "D";
  return "F";
}

/** Clamp a number into [min, max]. */
export function clamp(n: number, min = 0, max = 100): number {
  return Math.max(min, Math.min(max, n));
}

/** Normalize a list of point-based checks to a 0..100 pillar score. */
export function checksToScore(
  checks: Array<{ score: number; max: number }>,
): number {
  const max = checks.reduce((a, c) => a + c.max, 0);
  if (max <= 0) return 0;
  const got = checks.reduce((a, c) => a + Math.max(0, Math.min(c.score, c.max)), 0);
  return Math.round((got / max) * 100);
}

/** Normalize and validate a user-supplied URL. Throws on invalid/unsafe input. */
export function normalizeUrl(input: string): string {
  let raw = (input || "").trim();
  if (!raw) throw new Error("Please enter a URL.");
  if (!/^https?:\/\//i.test(raw)) raw = `https://${raw}`;
  let parsed: URL;
  try {
    parsed = new URL(raw);
  } catch {
    throw new Error("That doesn't look like a valid URL.");
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error("Only http(s) URLs are supported.");
  }
  return parsed.toString();
}

/** Color token for a status, used by UI components. */
export function statusColor(status: string): string {
  switch (status) {
    case "pass":
      return "text-good";
    case "warn":
      return "text-warn";
    case "fail":
      return "text-bad";
    default:
      return "text-slate-400";
  }
}

export function gradeColor(grade: Grade): string {
  switch (grade) {
    case "A":
    case "B":
      return "text-good";
    case "C":
      return "text-warn";
    default:
      return "text-bad";
  }
}
