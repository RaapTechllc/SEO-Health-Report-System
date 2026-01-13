import React from 'react';
import ScoreRadial from './charts/ScoreRadial';
import { useAnimatedScore } from '../hooks/useAnimatedScore';

export default function ScoreGauge({ score, size = "lg" }) {
  const animatedScore = useAnimatedScore(score);
  const chartSize = size === "lg" ? 200 : 120;

  return (
    <ScoreRadial score={animatedScore} size={chartSize} />
  );
}
