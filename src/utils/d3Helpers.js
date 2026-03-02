/**
 * D3.js helper utilities for the Divine Comedy visualization.
 */
import * as d3 from 'd3';

/**
 * Create a responsive SVG that resizes with its container.
 */
export function createResponsiveSvg(container, width, height, margin = { top: 20, right: 20, bottom: 30, left: 40 }) {
  const svg = d3.select(container)
    .append('svg')
    .attr('viewBox', `0 0 ${width} ${height}`)
    .attr('preserveAspectRatio', 'xMidYMid meet')
    .style('width', '100%')
    .style('height', '100%');

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);

  return {
    svg,
    g,
    innerWidth: width - margin.left - margin.right,
    innerHeight: height - margin.top - margin.bottom,
  };
}

/**
 * Realm color scales for D3.
 */
export const realmColorScale = d3.scaleOrdinal()
  .domain(['Inferno', 'Purgatorio', 'Paradiso'])
  .range(['#DC2626', '#A3824A', '#3B82F6']);

export const realmGradientScale = d3.scaleOrdinal()
  .domain(['Inferno', 'Purgatorio', 'Paradiso'])
  .range([
    ['#4B0082', '#8B0000', '#FF4500'],
    ['#8B7355', '#696969', '#556B2F'],
    ['#1E90FF', '#FFD700', '#F0F8FF'],
  ]);

/**
 * Create a full-journey color scale (canto 1-100).
 */
export function journeyColorScale() {
  return d3.scaleLinear()
    .domain([1, 34, 35, 67, 68, 100])
    .range(['#4B0082', '#FF4500', '#8B7355', '#556B2F', '#1E90FF', '#FFD700']);
}

/**
 * Add a tooltip div to the body if not already present.
 */
export function ensureTooltip() {
  let tooltip = d3.select('#d3-tooltip');
  if (tooltip.empty()) {
    tooltip = d3.select('body')
      .append('div')
      .attr('id', 'd3-tooltip')
      .style('position', 'fixed')
      .style('pointer-events', 'none')
      .style('background', 'rgba(10, 10, 20, 0.95)')
      .style('color', '#e0e0e0')
      .style('padding', '10px 14px')
      .style('border-radius', '6px')
      .style('font-size', '13px')
      .style('line-height', '1.5')
      .style('max-width', '320px')
      .style('border', '1px solid rgba(255,255,255,0.15)')
      .style('box-shadow', '0 4px 20px rgba(0,0,0,0.5)')
      .style('z-index', '10000')
      .style('opacity', 0);
  }
  return tooltip;
}

export function showTooltip(tooltip, html, event) {
  tooltip
    .html(html)
    .style('opacity', 1)
    .style('left', `${event.clientX + 15}px`)
    .style('top', `${event.clientY - 10}px`);
}

export function hideTooltip(tooltip) {
  tooltip.style('opacity', 0);
}

/**
 * Sentiment color: negative=red, neutral=gray, positive=gold/blue.
 */
export function sentimentColor(score) {
  if (score < -0.1) return d3.interpolateRgb('#8B0000', '#FF4500')(Math.min(1, (score + 1) / 0.9));
  if (score > 0.1) return d3.interpolateRgb('#556B2F', '#FFD700')(Math.min(1, (score - 0.1) / 0.9));
  return '#696969';
}
