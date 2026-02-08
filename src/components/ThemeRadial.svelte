<script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';
  import { ensureTooltip, showTooltip, hideTooltip, realmColorScale } from '../utils/d3Helpers.js';

  let { themes = [], realmThemes = {} } = $props();

  let container;
  let width = $state(700);
  let height = $state(700);
  let selectedRealm = $state('All');

  onMount(() => {
    const ro = new ResizeObserver(entries => {
      for (const entry of entries) {
        const size = Math.min(entry.contentRect.width, 700);
        width = size;
        height = size;
      }
    });
    ro.observe(container.parentElement);
    return () => ro.disconnect();
  });

  $effect(() => {
    if (themes.length && container && width && height) {
      drawRadial();
    }
  });

  function drawRadial() {
    const svg = d3.select(container);
    svg.selectAll('*').remove();

    const tooltip = ensureTooltip();
    const cx = width / 2;
    const cy = height / 2;
    const maxRadius = Math.min(width, height) / 2 - 60;
    const innerRadius = 50;

    const g = svg.append('g').attr('transform', `translate(${cx},${cy})`);

    // Get data based on selected realm
    let displayThemes;
    if (selectedRealm === 'All') {
      displayThemes = themes.map(t => ({
        name: t.name,
        value: t.total_frequency,
        description: t.description,
      }));
    } else {
      displayThemes = themes.map(t => ({
        name: t.name,
        value: t.by_realm[selectedRealm] || 0,
        description: t.description,
      })).filter(t => t.value > 0);
    }

    displayThemes.sort((a, b) => b.value - a.value);
    if (!displayThemes.length) return;

    const maxVal = d3.max(displayThemes, d => d.value);
    const radiusScale = d3.scaleLinear()
      .domain([0, maxVal])
      .range([innerRadius, maxRadius]);

    const angleStep = (Math.PI * 2) / displayThemes.length;

    // Draw concentric rings (guides)
    const tickValues = [0.25, 0.5, 0.75, 1].map(t => maxVal * t);
    tickValues.forEach(val => {
      g.append('circle')
        .attr('r', radiusScale(val))
        .attr('fill', 'none')
        .attr('stroke', '#333')
        .attr('stroke-width', 0.5)
        .attr('stroke-dasharray', '2,4');
    });

    // Theme color palette
    const themeColors = d3.scaleOrdinal()
      .domain(displayThemes.map(d => d.name))
      .range([
        '#DC2626', '#F59E0B', '#10B981', '#3B82F6', '#8B5CF6',
        '#EC4899', '#EF4444', '#F97316', '#14B8A6', '#6366F1',
        '#A855F7', '#F43F5E', '#D97706', '#059669', '#2563EB',
        '#7C3AED',
      ]);

    // Draw spokes and bars
    displayThemes.forEach((theme, i) => {
      const angle = i * angleStep - Math.PI / 2;
      const endRadius = radiusScale(theme.value);
      const x1 = 0;
      const y1 = 0;
      const x2 = Math.cos(angle) * endRadius;
      const y2 = Math.sin(angle) * endRadius;

      // Spoke line
      g.append('line')
        .attr('x1', Math.cos(angle) * innerRadius)
        .attr('y1', Math.sin(angle) * innerRadius)
        .attr('x2', x2)
        .attr('y2', y2)
        .attr('stroke', themeColors(theme.name))
        .attr('stroke-width', 3)
        .attr('stroke-opacity', 0.7)
        .attr('stroke-linecap', 'round');

      // End dot
      g.append('circle')
        .attr('cx', x2)
        .attr('cy', y2)
        .attr('r', 5)
        .attr('fill', themeColors(theme.name))
        .attr('stroke', '#111')
        .attr('stroke-width', 1)
        .attr('cursor', 'pointer')
        .on('mouseenter', function(event) {
          d3.select(this).transition().duration(100).attr('r', 9);
          const byRealmStr = Object.entries(theme.by_realm || {})
            .map(([r, v]) => `${r}: ${v}`)
            .join('<br/>');
          showTooltip(tooltip, `
            <div style="font-weight:bold;color:${themeColors(theme.name)};font-size:14px;">
              ${theme.name}
            </div>
            <div style="margin-top:4px;">
              <span style="color:#999">Frequency:</span> ${theme.value}<br/>
              ${theme.description ? `<span style="color:#999">Description:</span> ${theme.description}<br/>` : ''}
            </div>
          `, event);
        })
        .on('mouseleave', function() {
          d3.select(this).transition().duration(100).attr('r', 5);
          hideTooltip(tooltip);
        });

      // Label
      const labelRadius = maxRadius + 20;
      const lx = Math.cos(angle) * labelRadius;
      const ly = Math.sin(angle) * labelRadius;
      const rotation = (angle * 180 / Math.PI);
      const flip = (angle > Math.PI / 2 || angle < -Math.PI / 2);

      g.append('text')
        .attr('x', lx)
        .attr('y', ly)
        .attr('text-anchor', flip ? 'end' : 'start')
        .attr('dominant-baseline', 'middle')
        .attr('transform', `rotate(${flip ? rotation + 180 : rotation},${lx},${ly})`)
        .attr('fill', themeColors(theme.name))
        .attr('font-size', '11px')
        .attr('font-family', "'EB Garamond', Georgia, serif")
        .attr('opacity', 0.9)
        .text(theme.name);
    });

    // Center label
    g.append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('fill', '#888')
      .attr('font-size', '11px')
      .attr('font-family', "'EB Garamond', Georgia, serif")
      .text('Themes');

    // Title
    svg.append('text')
      .attr('x', width / 2).attr('y', 20)
      .attr('text-anchor', 'middle')
      .attr('fill', '#c0c0c0')
      .attr('font-size', '15px')
      .attr('font-family', "'EB Garamond', Georgia, serif")
      .text('Thematic Radial Map');
  }
</script>

<div class="radial-container">
  <div class="realm-filter">
    {#each ['All', 'Inferno', 'Purgatorio', 'Paradiso'] as realm}
      <button
        class="filter-btn"
        class:active={selectedRealm === realm}
        onclick={() => { selectedRealm = realm; }}
      >
        {realm}
      </button>
    {/each}
  </div>
  <svg bind:this={container} {width} {height}></svg>
</div>

<style>
  .radial-container {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .realm-filter {
    display: flex;
    gap: 8px;
    justify-content: center;
    margin-bottom: 10px;
  }
  .filter-btn {
    background: transparent;
    color: #aaa;
    border: 1px solid #444;
    padding: 4px 14px;
    border-radius: 16px;
    cursor: pointer;
    font-size: 12px;
    font-family: 'EB Garamond', Georgia, serif;
    transition: all 0.2s;
  }
  .filter-btn:hover { color: #fff; border-color: #888; }
  .filter-btn.active { color: #fff; background: rgba(255,255,255,0.08); border-color: #aaa; }
  svg { overflow: visible; }
</style>
