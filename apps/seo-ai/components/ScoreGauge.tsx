import type { Grade } from "@/lib/types";
import { clamp, gradeColor } from "@/lib/utils";

/** Map a grade to an SVG stroke color (currentColor classes don't apply to SVG stroke reliably). */
function gradeStroke(grade: Grade): string {
  switch (grade) {
    case "A":
    case "B":
      return "#22c55e"; // good
    case "C":
      return "#f59e0b"; // warn
    default:
      return "#ef4444"; // bad
  }
}

export default function ScoreGauge({
  score,
  grade,
  size = 160,
}: {
  score: number;
  grade: Grade;
  size?: number;
}) {
  const value = clamp(Math.round(score));
  const stroke = Math.max(6, Math.round(size * 0.08));
  const radius = (size - stroke) / 2;
  const center = size / 2;
  const circumference = 2 * Math.PI * radius;
  const dash = (value / 100) * circumference;
  const color = gradeStroke(grade);

  return (
    <div
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
      role="img"
      aria-label={`Score ${value} out of 100, grade ${grade}`}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="-rotate-90"
      >
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="currentColor"
          className="text-slate-200"
          strokeWidth={stroke}
        />
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circumference}`}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="font-bold leading-none tabular-nums"
          style={{ fontSize: size * 0.3 }}
        >
          {value}
        </span>
        <span
          className={`font-semibold leading-none ${gradeColor(grade)}`}
          style={{ fontSize: size * 0.16 }}
        >
          {grade}
        </span>
      </div>
    </div>
  );
}
