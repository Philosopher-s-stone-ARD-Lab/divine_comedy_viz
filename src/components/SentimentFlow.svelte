<script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';
  import { ensureTooltip, showTooltip, hideTooltip, journeyColorScale } from '../utils/d3Helpers.js';

  let { cantos = [], onCantoSelect = () => {} } = $props();

  let container;
  let width = $state(900);
  let height = $state(350);

  onMount(() => {
    const ro = new ResizeObserver(entries => {
      for (const entry of entries) {
        width = entry.contentRect.width;
      }
    });
    ro.observe(container.parentElement);
    return () => ro.disconnect();
  });

  $effect(() => {
    if (cantos.length && container && width) {
      drawChart();
    }
  });

  function drawChart() {
    const svg = d3.select(container);
    svg.selectAll('*').remove();

    const tooltip = ensureTooltip();
    const colorScale = journeyColorScale();
    const margin = { top: 30, right: 30, bottom: 45, left: 55 };
    const w = width - margin.left - margin.right;
    const h = height - margin.top - margin.bottom;

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    // Scales
    const x = d3.scaleLinear()
      .domain([1, cantos.length])
      .range([0, w]);

    const sentimentExtent = d3.extent(cantos, d => d.sentiment.compound);
    const y = d3.scaleLinear()
      .domain([Math.min(-1, sentimentExtent[0] - 0.05), Math.max(1, sentimentExtent[1] + 0.05)])
      .range([h, 0]);

    // Realm background bands
    const realmBands = [
      { name: 'Inferno', start: 1, end: 34, color: '#8B0000' },
      { name: 'Purgatorio', start: 35, end: 67, color: '#8B7355' },
      { name: 'Paradiso', start: 68, end: 100, color: '#1E90FF' },
    ];

    realmBands.forEach(band => {
      g.append('rect')
        .attr('x', x(band.start))
        .attr('y', 0)
        .attr('width', x(band.end) - x(band.start))
        .attr('height', h)
        .attr('fill', band.color)
        .attr('opacity', 0.06);

      g.append('text')
        .attr('x', x((band.start + band.end) / 2))
        .attr('y', -10)
        .attr('text-anchor', 'middle')
        .attr('fill', band.color)
        .attr('font-size', '11px')
        .attr('font-family', "'EB Garamond', Georgia, serif")
        .attr('opacity', 0.7)
        .text(band.name);
    });

    // Zero line
    g.append('line')
      .attr('x1', 0).attr('x2', w)
      .attr('y1', y(0)).attr('y2', y(0))
      .attr('stroke', '#444')
      .attr('stroke-dasharray', '4,4')
      .attr('stroke-width', 1);

    // Area chart - positive area
    const areaPositive = d3.area()
      .x(d => x(d.global_number))
      .y0(y(0))
      .y1(d => y(Math.max(0, d.sentiment.compound)))
      .curve(d3.curveCatmullRom.alpha(0.5));

    g.append('path')
      .datum(cantos)
      .attr('d', areaPositive)
      .attr('fill', 'url(#positiveGrad)')
      .attr('opacity', 0.3);

    // Area chart - negative area
    const areaNegative = d3.area()
      .x(d => x(d.global_number))
      .y0(y(0))
      .y1(d => y(Math.min(0, d.sentiment.compound)))
      .curve(d3.curveCatmullRom.alpha(0.5));

    g.append('path')
      .datum(cantos)
      .attr('d', areaNegative)
      .attr('fill', 'url(#negativeGrad)')
      .attr('opacity', 0.3);

    // Gradients
    const defs = svg.append('defs');

    const posGrad = defs.append('linearGradient')
      .attr('id', 'positiveGrad').attr('x1', '0').attr('y1', '1').attr('x2', '0').attr('y2', '0');
    posGrad.append('stop').attr('offset', '0%').attr('stop-color', '#556B2F').attr('stop-opacity', 0);
    posGrad.append('stop').attr('offset', '100%').attr('stop-color', '#FFD700').attr('stop-opacity', 0.7);

    const negGrad = defs.append('linearGradient')
      .attr('id', 'negativeGrad').attr('x1', '0').attr('y1', '0').attr('x2', '0').attr('y2', '1');
    negGrad.append('stop').attr('offset', '0%').attr('stop-color', '#FF4500').attr('stop-opacity', 0);
    negGrad.append('stop').attr('offset', '100%').attr('stop-color', '#8B0000').attr('stop-opacity', 0.7);

    // Line
    const line = d3.line()
      .x(d => x(d.global_number))
      .y(d => y(d.sentiment.compound))
      .curve(d3.curveCatmullRom.alpha(0.5));

    g.append('path')
      .datum(cantos)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', '#e0e0e0')
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.8);

    // Data points
    g.selectAll('.sentiment-dot')
      .data(cantos)
      .join('circle')
      .attr('class', 'sentiment-dot')
      .attr('cx', d => x(d.global_number))
      .attr('cy', d => y(d.sentiment.compound))
      .attr('r', 3.5)
      .attr('fill', d => colorScale(d.global_number))
      .attr('stroke', '#111')
      .attr('stroke-width', 0.5)
      .attr('cursor', 'pointer')
      .on('mouseenter', function(event, d) {
        d3.select(this).transition().duration(100).attr('r', 7);
        showTooltip(tooltip, `
          <div style="font-weight:bold;color:${colorScale(d.global_number)}">
            ${d.realm}: ${d.title}
          </div>
          <div style="margin-top:4px;">
            <span style="color:#999">Sentiment:</span> ${d.sentiment.compound.toFixed(3)}<br/>
            <span style="color:#999">Positive:</span> ${d.sentiment.positive.toFixed(3)}<br/>
            <span style="color:#999">Negative:</span> ${d.sentiment.negative.toFixed(3)}<br/>
            <span style="color:#999">Location:</span> ${d.location}
          </div>
        `, event);
      })
      .on('mouseleave', function() {
        d3.select(this).transition().duration(100).attr('r', 3.5);
        hideTooltip(tooltip);
      })
      .on('click', (event, d) => onCantoSelect(d.global_number));

    // Axes
    const xAxis = d3.axisBottom(x).ticks(10).tickFormat(d => `${d}`);
    g.append('g')
      .attr('transform', `translate(0,${h})`)
      .call(xAxis)
      .selectAll('text').attr('fill', '#888').attr('font-size', '10px');
    g.selectAll('.domain, .tick line').attr('stroke', '#444');

    g.append('text')
      .attr('x', w / 2).attr('y', h + 35)
      .attr('text-anchor', 'middle')
      .attr('fill', '#888')
      .attr('font-size', '11px')
      .text('Canto Number');

    const yAxis = d3.axisLeft(y).ticks(5);
    g.append('g').call(yAxis)
      .selectAll('text').attr('fill', '#888').attr('font-size', '10px');

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -h / 2).attr('y', -40)
      .attr('text-anchor', 'middle')
      .attr('fill', '#888')
      .attr('font-size', '11px')
      .text('Sentiment Score');

    // Title
    svg.append('text')
      .attr('x', width / 2).attr('y', 18)
      .attr('text-anchor', 'middle')
      .attr('fill', '#c0c0c0')
      .attr('font-size', '15px')
      .attr('font-family', "'EB Garamond', Georgia, serif")
      .text('Emotional Arc of the Journey');
  }
</script>

<div class="sentiment-container">
  <svg bind:this={container} {width} {height}></svg>
</div>

<style>
  .sentiment-container {
    width: 100%;
  }
  svg {
    overflow: visible;
  }
</style>
