<script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';
  import { ensureTooltip, showTooltip, hideTooltip, realmColorScale } from '../utils/d3Helpers.js';

  let { networkData = null, onCantoSelect = () => {} } = $props();

  let container;
  let width = $state(800);
  let height = $state(600);
  let selectedRealm = $state('All');

  onMount(() => {
    const ro = new ResizeObserver(entries => {
      for (const entry of entries) {
        width = entry.contentRect.width;
        height = Math.max(450, entry.contentRect.height);
      }
    });
    ro.observe(container.parentElement);
    return () => ro.disconnect();
  });

  $effect(() => {
    if (networkData && container && width && height) {
      drawNetwork();
    }
  });

  function drawNetwork() {
    const svg = d3.select(container);
    svg.selectAll('*').remove();

    const tooltip = ensureTooltip();

    // Filter by realm
    let nodes = networkData.nodes.map(n => ({ ...n }));
    let links = networkData.links.map(l => ({ ...l }));

    if (selectedRealm !== 'All') {
      nodes = nodes.filter(n => n.realm_association.includes(selectedRealm));
      const nodeIds = new Set(nodes.map(n => n.id));
      links = links.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target));
    }

    // Filter to only nodes with connections
    const connectedIds = new Set();
    links.forEach(l => { connectedIds.add(l.source); connectedIds.add(l.target); });
    nodes = nodes.filter(n => connectedIds.has(n.id));

    if (!nodes.length) return;

    // Scales
    const mentionExtent = d3.extent(nodes, n => n.mentions);
    const nodeSize = d3.scaleSqrt().domain(mentionExtent).range([4, 22]);
    const linkWidth = d3.scaleLinear().domain(d3.extent(links, l => l.weight)).range([0.5, 4]);
    const linkOpacity = d3.scaleLinear().domain(d3.extent(links, l => l.weight)).range([0.1, 0.5]);

    function nodeColor(d) {
      if (d.realm_association.length === 1) return realmColorScale(d.realm_association[0]);
      if (d.realm_association.includes('Paradiso')) return '#3B82F6';
      if (d.realm_association.includes('Purgatorio')) return '#A3824A';
      return '#DC2626';
    }

    // Force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(80).strength(0.3))
      .force('charge', d3.forceManyBody().strength(-150))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => nodeSize(d.mentions) + 5));

    // Draw links
    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#555')
      .attr('stroke-width', d => linkWidth(d.weight))
      .attr('stroke-opacity', d => linkOpacity(d.weight));

    // Draw nodes
    const node = svg.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    node.append('circle')
      .attr('r', d => nodeSize(d.mentions))
      .attr('fill', d => nodeColor(d))
      .attr('stroke', '#222')
      .attr('stroke-width', 1.5)
      .attr('opacity', 0.85);

    // Labels for prominent characters
    node.filter(d => d.mentions >= 5)
      .append('text')
      .text(d => d.id)
      .attr('dy', d => nodeSize(d.mentions) + 12)
      .attr('text-anchor', 'middle')
      .attr('fill', '#ccc')
      .attr('font-size', '10px')
      .attr('font-family', "'EB Garamond', Georgia, serif")
      .attr('pointer-events', 'none');

    // Tooltip interactions
    node.on('mouseenter', function(event, d) {
      d3.select(this).select('circle')
        .transition().duration(150)
        .attr('r', nodeSize(d.mentions) * 1.4)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);

      // Highlight connections
      link.attr('stroke-opacity', l =>
        (l.source.id === d.id || l.target.id === d.id) ? 0.8 : 0.05
      ).attr('stroke', l =>
        (l.source.id === d.id || l.target.id === d.id) ? nodeColor(d) : '#555'
      );

      showTooltip(tooltip, `
        <div style="font-weight:bold;color:${nodeColor(d)};font-size:14px;">${d.id}</div>
        <div style="margin-top:4px;">
          <span style="color:#999">Role:</span> ${d.role}<br/>
          <span style="color:#999">Appears in:</span> ${d.mentions} cantos<br/>
          <span style="color:#999">Realms:</span> ${d.realm_association.join(', ')}<br/>
          <span style="color:#999">Significance:</span> ${d.significance || 'N/A'}
        </div>
      `, event);
    })
    .on('mouseleave', function(event, d) {
      d3.select(this).select('circle')
        .transition().duration(150)
        .attr('r', nodeSize(d.mentions))
        .attr('stroke', '#222')
        .attr('stroke-width', 1.5);

      link.attr('stroke-opacity', l => linkOpacity(l.weight))
        .attr('stroke', '#555');
      hideTooltip(tooltip);
    });

    // Simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x; d.fy = d.y;
    }
    function dragged(event, d) {
      d.fx = event.x; d.fy = event.y;
    }
    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null; d.fy = null;
    }

    // Title
    svg.append('text')
      .attr('x', width / 2).attr('y', 20)
      .attr('text-anchor', 'middle')
      .attr('fill', '#c0c0c0')
      .attr('font-size', '15px')
      .attr('font-family', "'EB Garamond', Georgia, serif")
      .text('Character Relationships');
  }
</script>

<div class="network-container">
  <div class="realm-filter">
    {#each ['All', 'Inferno', 'Purgatorio', 'Paradiso'] as realm}
      <button
        class="filter-btn"
        class:active={selectedRealm === realm}
        style={realm !== 'All' ? `border-color: ${realmColorScale(realm)}` : ''}
        onclick={() => { selectedRealm = realm; }}
      >
        {realm}
      </button>
    {/each}
  </div>
  <svg bind:this={container} {width} {height}></svg>
</div>

<style>
  .network-container {
    width: 100%;
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
  .filter-btn:hover {
    color: #fff;
    border-color: #888;
  }
  .filter-btn.active {
    color: #fff;
    background: rgba(255,255,255,0.08);
    border-color: #aaa;
  }
  svg {
    overflow: visible;
  }
</style>
