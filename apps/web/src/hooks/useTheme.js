import { useEffect, useMemo } from 'react';

// Simplified color generation helper
// Ideally we would use a library like 'tinycolor2' or 'colord', but to avoid deps we'll use a simple lighten/darken
function adjustColor(color, amount) {
    return '#' + color.replace(/^#/, '').replace(/../g, color => ('0' + Math.min(255, Math.max(0, parseInt(color, 16) + amount)).toString(16)).substr(-2));
}

// Convert hex to rgb for better manipulation if needed, but for now simple hex manip
// A better approach without libs is hardcoding a palette generation or just relying on opacity
// But to make it "extravagant" we want real shades. 
// Let's assume we pass in a primary color and generate shades by mixing with white/black
function getShades(hex) {
    // Check if valid hex
    if (!/^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/.test(hex)) return null;

    // Quick and dirty shade generator (not perfect but works for demo)
    // Real implementation would use HSL manipulation
    return {
        50: adjustColor(hex, 180),
        100: adjustColor(hex, 160),
        200: adjustColor(hex, 120),
        300: adjustColor(hex, 80),
        400: adjustColor(hex, 40),
        500: hex,
        600: adjustColor(hex, -20),
        700: adjustColor(hex, -40),
        800: adjustColor(hex, -60),
        900: adjustColor(hex, -80),
    };
}

export function useTheme(primaryColor) {
    useEffect(() => {
        if (!primaryColor) return;

        const shades = getShades(primaryColor);
        if (!shades) return;

        const root = document.documentElement;
        Object.entries(shades).forEach(([key, value]) => {
            root.style.setProperty(`--brand-${key}`, value);
        });

    }, [primaryColor]);
}
