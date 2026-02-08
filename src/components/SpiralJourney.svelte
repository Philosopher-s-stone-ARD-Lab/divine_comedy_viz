<script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';
  import { ensureTooltip, showTooltip, hideTooltip, journeyColorScale } from '../utils/d3Helpers.js';
  import { getRealmColor } from '../utils/dataProcessing.js';

  let { journeyData = [], mainData = null, onCantoSelect = () => {} } = $props();

  let container;
  let width = $state(900);
  let height = $state(700);

  onMount(() => {
    if (journeyData.length && container) {
      drawSpiral();
    }
    const ro = new ResizeObserver(entries => {
      for (const entry of entries) {
        width = entry.contentRect.width;
        height = Math.max(500, entry.contentRect.height);
      }
    });
    ro.observe(container);
    return () => ro.disconnect();
  });

  $effect(() => {
    if (journeyData.length && container && width && height) {
      drawSpiral();
    }
  });

  function drawSpiral() {
    const svg = d3.select(container);
    svg.selectAll('*').remove();

    const tooltip = ensureTooltip();
    const colorScale = journeyColorScale();
    const margin = { top: 40, right: 40, bottom: 40, left: 40 };
    const w = width - margin.left - margin.right;
    const h = height - margin.top - margin.bottom;
    const cx = w / 2 + margin.left;
    const cy = h / 2 + margin.top;

    const g = svg.append('g');

    // Realm labels and background arcs
    const realmRanges = [
      { name: 'Inferno', start: 1, end: 34, color: '#8B0000' },
      { name: 'Purgatorio', start: 35, end: 67, color: '#8B7355' },
      { name: 'Paradiso', start: 68, end: 100, color: '#1E90FF' },
    ];

    // Scale: map canto global number to angle and radius
    const maxRadius = Math.min(w, h) / 2 - 20;
    const minRadius = 30;

    const points = journeyData.map(d => {
      const t = (d.global_canto - 1) / 99; // 0 to 1
      const angle = t * Math.PI * 4 - Math.PI / 2; // ~2 full rotations
      const radius = minRadius + t * (maxRadius - minRadius);
      return {
        ...d,
        cx: cx + Math.cos(angle) * radius,
        cy: cy + Math.sin(angle) * radius,
        radius: radius,
        angle: angle,
      };
    });

    // Draw spiral path
    const line = d3.line()
      .x(d => d.cx)
      .y(d => d.cy)
      .curve(d3.curveCatmullRom.alpha(0.5));

    // Draw realm background segments on the spiral
    realmRanges.forEach(realm => {
      const realmPoints = points.filter(p => p.global_canto >= realm.start && p.global_canto <= realm.end);
      if (realmPoints.length < 2) return;
      g.append('path')
        .datum(realmPoints)
        .attr('d', line)
        .attr('fill', 'none')
        .attr('stroke', realm.color)
        .attr('stroke-width', 3)
        .attr('stroke-opacity', 0.25);
    });

    // Draw connecting path
    g.append('path')
      .datum(points)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', 'url(#spiralGradient)')
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.5);

    // Define gradient
    const defs = svg.append('defs');
    const gradient = defs.append('linearGradient')
      .attr('id', 'spiralGradient')
      .attr('gradientUnits', 'userSpaceOnUse')
      .attr('x1', points[0]?.cx || 0)
      .attr('y1', points[0]?.cy || 0)
      .attr('x2', points[points.length - 1]?.cx || w)
      .attr('y2', points[points.length - 1]?.cy || h);

    gradient.append('stop').attr('offset', '0%').attr('stop-color', '#4B0082');
    gradient.append('stop').attr('offset', '34%').attr('stop-color', '#FF4500');
    gradient.append('stop').attr('offset', '50%').attr('stop-color', '#8B7355');
    gradient.append('stop').attr('offset', '67%').attr('stop-color', '#556B2F');
    gradient.append('stop').attr('offset', '100%').attr('stop-color', '#FFD700');

    // Word count scale for node size
    const wordExtent = d3.extent(journeyData, d => d.word_count);
    const sizeScale = d3.scaleSqrt()
      .domain(wordExtent)
      .range([3, 10]);

    // Draw canto nodes
    const nodes = g.selectAll('.canto-node')
      .data(points)
      .join('circle')
      .attr('class', 'canto-node')
      .attr('cx', d => d.cx)
      .attr('cy', d => d.cy)
      .attr('r', d => sizeScale(d.word_count))
      .attr('fill', d => colorScale(d.global_canto))
      .attr('stroke', '#fff')
      .attr('stroke-width', 0.5)
      .attr('stroke-opacity', 0.5)
      .attr('cursor', 'pointer')
      .style('filter', d => d.sentiment > 0.5 ? 'drop-shadow(0 0 3px gold)' : d.sentiment < -0.5 ? 'drop-shadow(0 0 3px #ff0000)' : 'none');

    // Interactions
    nodes.on('mouseenter', function(event, d) {
      d3.select(this)
        .transition().duration(150)
        .attr('r', sizeScale(d.word_count) * 1.8)
        .attr('stroke-width', 2)
        .attr('stroke', '#fff');

      const allCantos = mainData?.realms?.flatMap(r => r.cantos) || [];
      const cantoData = allCantos.find(c => c.global_number === d.global_canto);
      const chars = cantoData?.characters?.slice(0, 3).map(c => c.name).join(', ') || 'None';
      const themes = cantoData?.key_themes?.slice(0, 3).map(t => t.theme).join(', ') || 'None';

      showTooltip(tooltip, `
        <div style="font-weight:bold;color:${colorScale(d.global_canto)};font-size:14px;">
          ${d.realm}: ${d.title}
        </div>
        <div style="margin-top:4px;">
          <span style="color:#999">Location:</span> ${d.location}<br/>
          <span style="color:#999">Words:</span> ${d.word_count}<br/>
          <span style="color:#999">Sentiment:</span> ${d.sentiment.toFixed(3)}<br/>
          <span style="color:#999">Theme:</span> ${d.dominant_theme}<br/>
          <span style="color:#999">Characters:</span> ${chars}<br/>
          <span style="color:#999">Themes:</span> ${themes}
        </div>
      `, event);
    })
    .on('mouseleave', function(event, d) {
      d3.select(this)
        .transition().duration(150)
        .attr('r', sizeScale(d.word_count))
        .attr('stroke-width', 0.5);
      hideTooltip(tooltip);
    })
    .on('click', (event, d) => {
      onCantoSelect(d.global_canto);
    });

    // Realm labels
    realmRanges.forEach(realm => {
      const midCanto = Math.floor((realm.start + realm.end) / 2);
      const midPoint = points.find(p => p.global_canto === midCanto);
      if (midPoint) {
        const labelAngle = midPoint.angle;
        const labelRadius = midPoint.radius + 25;
        g.append('text')
          .attr('x', cx + Math.cos(labelAngle) * labelRadius)
          .attr('y', cy + Math.sin(labelAngle) * labelRadius)
          .attr('text-anchor', 'middle')
          .attr('fill', realm.color)
          .attr('font-size', '13px')
          .attr('font-family', "'EB Garamond', 'Crimson Text', Georgia, serif")
          .attr('font-weight', 'bold')
          .attr('opacity', 0.8)
          .text(realm.name);
      }
    });

    // Title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', 24)
      .attr('text-anchor', 'middle')
      .attr('fill', '#c0c0c0')
      .attr('font-size', '16px')
      .attr('font-family', "'EB Garamond', 'Crimson Text', Georgia, serif")
      .text('The Journey Through the Divine Comedy');

    // Start animation
    nodes.attr('opacity', 0)
      .transition()
      .duration(20)
      .delay((d, i) => i * 20)
      .attr('opacity', 1);
  }
</script>

<div class="spiral-container">
  <svg bind:this={container} {width} {height}></svg>
</div>

<style>
  .spiral-container {
    width: 100%;
    height: 100%;
    min-height: 500px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  svg {
    overflow: visible;
  }
</style>
