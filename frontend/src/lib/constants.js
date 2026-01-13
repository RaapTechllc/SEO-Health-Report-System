export const GRADE_CONFIG = {
  A: { min: 90, color: 'score-excellent', label: 'Excellent' },
  B: { min: 80, color: 'score-good', label: 'Good' },
  C: { min: 70, color: 'score-fair', label: 'Fair' },
  D: { min: 60, color: 'score-poor', label: 'Poor' },
  F: { min: 0, color: 'score-critical', label: 'Critical' }
}

export function getGradeFromScore(score) {
  if (score >= 90) return 'A'
  if (score >= 80) return 'B'
  if (score >= 70) return 'C'
  if (score >= 60) return 'D'
  return 'F'
}