export const GRADE_CONFIG = {
    A: { min: 90, label: 'Excellent', color: 'score-excellent', bgClass: 'bg-green-100 text-green-700', message: 'Outstanding work!' },
    B: { min: 80, label: 'Good', color: 'score-good', bgClass: 'bg-green-100 text-green-700', message: 'Good, but room to grow.' },
    C: { min: 70, label: 'Needs Work', color: 'score-fair', bgClass: 'bg-amber-100 text-amber-700', message: 'Needs attention.' },
    D: { min: 60, label: 'Poor', color: 'score-poor', bgClass: 'bg-orange-100 text-orange-700', message: 'Significant improvements needed.' },
    F: { min: 0, label: 'Critical', color: 'score-critical', bgClass: 'bg-red-100 text-red-700', message: 'Critical issues detected.' },
}

export const getGradeFromScore = (score) => {
    if (score >= 90) return 'A'
    if (score >= 80) return 'B'
    if (score >= 70) return 'C'
    if (score >= 60) return 'D'
    return 'F'
}

export const getScoreColor = (score) => {
    if (score >= 90) return '#10b981'
    if (score >= 80) return '#22c55e'
    if (score >= 70) return '#f59e0b'
    if (score >= 60) return '#f97316'
    return '#ef4444'
}

export const getScoreTailwind = (score) => {
    if (score >= 90) return 'bg-emerald-500'
    if (score >= 80) return 'bg-green-500'
    if (score >= 70) return 'bg-amber-500'
    if (score >= 60) return 'bg-orange-500'
    return 'bg-red-500'
}
