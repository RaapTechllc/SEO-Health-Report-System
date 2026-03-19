import { useState, useEffect } from 'react';

export function useAnimatedScore(targetScore, duration = 1500) {
  const [currentScore, setCurrentScore] = useState(0);

  useEffect(() => {
    if (targetScore === 0) return;

    const startTime = Date.now();
    const startScore = 0;
    
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function for smooth animation
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      const newScore = Math.round(startScore + (targetScore - startScore) * easeOutQuart);
      
      setCurrentScore(newScore);
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    
    requestAnimationFrame(animate);
  }, [targetScore, duration]);

  return currentScore;
}