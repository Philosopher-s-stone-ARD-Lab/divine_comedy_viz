/**
 * Data processing utilities for the Divine Comedy visualization.
 */

/**
 * Load and parse a JSON data file from the /src/data directory.
 */
export async function loadData(filename) {
  const response = await fetch(`/src/data/${filename}`);
  if (!response.ok) throw new Error(`Failed to load ${filename}`);
  return response.json();
}

/**
 * Get all cantos as a flat array with realm info.
 */
export function getAllCantos(data) {
  if (!data?.realms) return [];
  return data.realms.flatMap(realm =>
    realm.cantos.map(c => ({ ...c, realmName: realm.name }))
  );
}

/**
 * Get the color for a realm.
 */
export const REALM_COLORS = {
  Inferno: { primary: '#8B0000', secondary: '#FF4500', tertiary: '#4B0082', bg: '#1a0000' },
  Purgatorio: { primary: '#8B7355', secondary: '#696969', tertiary: '#556B2F', bg: '#1a1a10' },
  Paradiso: { primary: '#1E90FF', secondary: '#FFD700', tertiary: '#F0F8FF', bg: '#000a1a' },
};

export function getRealmColor(realm, type = 'primary') {
  return REALM_COLORS[realm]?.[type] || '#666';
}

/**
 * Get a gradient color based on global canto number (1-100).
 */
export function getCantoColor(globalNumber) {
  if (globalNumber <= 34) {
    // Inferno: dark red to orange
    const t = globalNumber / 34;
    return interpolateColor('#4B0082', '#FF4500', t);
  } else if (globalNumber <= 67) {
    // Purgatorio: earthy to green
    const t = (globalNumber - 34) / 33;
    return interpolateColor('#8B7355', '#556B2F', t);
  } else {
    // Paradiso: blue to gold
    const t = (globalNumber - 67) / 33;
    return interpolateColor('#1E90FF', '#FFD700', t);
  }
}

function interpolateColor(color1, color2, t) {
  const r1 = parseInt(color1.slice(1, 3), 16);
  const g1 = parseInt(color1.slice(3, 5), 16);
  const b1 = parseInt(color1.slice(5, 7), 16);
  const r2 = parseInt(color2.slice(1, 3), 16);
  const g2 = parseInt(color2.slice(3, 5), 16);
  const b2 = parseInt(color2.slice(5, 7), 16);
  const r = Math.round(r1 + (r2 - r1) * t);
  const g = Math.round(g1 + (g2 - g1) * t);
  const b = Math.round(b1 + (b2 - b1) * t);
  return `rgb(${r},${g},${b})`;
}

/**
 * Format a sentiment score for display.
 */
export function formatSentiment(score) {
  if (score > 0.3) return 'Positive';
  if (score < -0.3) return 'Negative';
  return 'Neutral';
}

/**
 * Get top N items from an array by a key.
 */
export function topN(arr, n, key = 'count') {
  return [...arr].sort((a, b) => b[key] - a[key]).slice(0, n);
}
