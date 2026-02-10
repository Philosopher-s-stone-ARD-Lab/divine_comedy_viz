<script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';
  import { ensureTooltip, showTooltip, hideTooltip, realmColorScale } from '../utils/d3Helpers.js';

  let { networkData = null, onCantoSelect = () => {} } = $props();

  let container;
  let svgWrapper;
  let width = $state(800);
  let height = $state(600);
  let selectedRealm = $state('All');
  let currentSimulation = null;

  // Search state
  let searchQuery = $state('');
  let searchFocused = $state(false);
  let highlightedNode = $state(null);

  // Store D3 selections and scale functions for highlighting
  let d3Nodes = null;
  let d3Links = null;
  let d3NodeSize = null;
  let d3NodeColor = null;
  let d3NodeOpacity = null;
  let d3NodeStroke = null;
  let d3NodeStrokeWidth = null;
  let d3LinkOpacity = null;
  let currentNodes = [];
  let currentRealm = 'All';

  const suggestions = $derived(() => {
    if (!searchQuery || searchQuery.length < 1 || !currentNodes.length) return [];
    const q = searchQuery.toLowerCase();
    return currentNodes
      .filter(n => n.id.toLowerCase().includes(q))
      .slice(0, 8)
      .map(n => n.id);
  });

  function selectCharacter(name) {
    searchQuery = name;
    searchFocused = false;
    highlightedNode = name;
    highlightNodeInGraph(name);
  }

  function clearSearch() {
    searchQuery = '';
    highlightedNode = null;
    resetHighlight();
  }

  function highlightNodeInGraph(name) {
    if (!d3Nodes || !d3Links) return;

    // Find connected node IDs
    const connectedIds = new Set();
    d3Links.each(l => {
      if (l.source.id === name) connectedIds.add(l.target.id);
      if (l.target.id === name) connectedIds.add(l.source.id);
    });

    // Circles: selected = full, connected = visible, others = faded
    d3Nodes.select('circle')
      .transition().duration(300)
      .attr('opacity', d => {
        if (d.id === name) return 1;
        if (connectedIds.has(d.id)) return 0.75;
        return 0.06;
      })
      .attr('stroke', d => d.id === name ? '#fff' : '#222')
      .attr('stroke-width', d => d.id === name ? 2.5 : 1);

    // Labels: remove existing, then re-add for selected + connected
    d3Nodes.selectAll('text').remove();
    d3Nodes.filter(d => d.id === name || connectedIds.has(d.id))
      .append('text')
      .text(d => d.id)
      .attr('dy', d => d3NodeSize(d.mentions) + 12)
      .attr('text-anchor', 'middle')
      .attr('fill', d => d.id === name ? '#fff' : '#ccc')
      .attr('font-size', d => d.id === name ? '12px' : '10px')
      .attr('font-weight', d => d.id === name ? '600' : '400')
      .attr('font-family', "'EB Garamond', Georgia, serif")
      .attr('pointer-events', 'none')
      .attr('opacity', 0)
      .transition().duration(300)
      .attr('opacity', 1);

    // Links: show connected, almost hide others
    d3Links
      .transition().duration(300)
      .attr('stroke-opacity', l =>
        (l.source.id === name || l.target.id === name) ? 0.7 : 0.015
      )
      .attr('stroke', l =>
        (l.source.id === name || l.target.id === name)
          ? d3NodeColor(l.source.id === name ? l.source : l.target)
          : '#555'
      );
  }

  function resetHighlight() {
    if (!d3Nodes || !d3Links || !d3NodeColor || !d3LinkOpacity) return;

    d3Nodes.select('circle')
      .transition().duration(300)
      .attr('opacity', d => d3NodeOpacity(d))
      .attr('stroke', d => d3NodeStroke(d))
      .attr('stroke-width', d => d3NodeStrokeWidth(d));

    // Restore original labels: remove all, re-add for mentions >= 5
    d3Nodes.selectAll('text').remove();
    d3Nodes.filter(d => d.mentions >= 5)
      .append('text')
      .text(d => d.id)
      .attr('dy', d => d3NodeSize(d.mentions) + 12)
      .attr('text-anchor', 'middle')
      .attr('fill', '#ccc')
      .attr('font-size', '10px')
      .attr('font-family', "'EB Garamond', Georgia, serif")
      .attr('pointer-events', 'none');

    d3Links
      .transition().duration(300)
      .attr('stroke-opacity', l => d3LinkOpacity(l.weight))
      .attr('stroke', '#555');
  }

  onMount(() => {
    const ro = new ResizeObserver(entries => {
      for (const entry of entries) {
        const w = entry.contentRect.width;
        const h = entry.contentRect.height;
        if (w > 0) width = w;
        if (h > 0) height = h;
      }
    });
    ro.observe(svgWrapper);
    return () => {
      ro.disconnect();
      if (currentSimulation) currentSimulation.stop();
    };
  });

  // Full redraw when data or realm filter changes
  $effect(() => {
    if (networkData && container && width && height) {
      // Read selectedRealm to track it
      const realm = selectedRealm;
      drawNetwork(realm);
    }
  });

  function drawNetwork(realm) {
    if (currentSimulation) {
      currentSimulation.stop();
      currentSimulation = null;
    }

    const svg = d3.select(container);
    svg.selectAll('*').remove();

    const tooltip = ensureTooltip();

    // Filter by realm
    let nodes = networkData.nodes.map(n => ({ ...n }));
    let links = networkData.links.map(l => ({ ...l }));

    if (realm !== 'All') {
      nodes = nodes.filter(n => n.realm_association.includes(realm));
      const nodeIds = new Set(nodes.map(n => n.id));
      links = links.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target));
    }

    // Filter to only nodes with connections
    const connectedIds = new Set();
    links.forEach(l => { connectedIds.add(l.source); connectedIds.add(l.target); });
    nodes = nodes.filter(n => connectedIds.has(n.id));

    if (!nodes.length) return;

    // Initialize node positions near center to avoid (0,0) clustering
    const cx = width / 2;
    const cy = height / 2;
    nodes.forEach((n, i) => {
      const angle = (i / nodes.length) * 2 * Math.PI;
      const r = 50 + Math.random() * 100;
      n.x = cx + r * Math.cos(angle);
      n.y = cy + r * Math.sin(angle);
    });

    // Scales
    const mentionExtent = d3.extent(nodes, n => n.mentions);
    const nodeSize = d3.scaleSqrt().domain(mentionExtent).range([4, 22]);
    const linkWidth = d3.scaleLinear().domain(d3.extent(links, l => l.weight)).range([0.5, 4]);
    const linkOpacity = d3.scaleLinear().domain(d3.extent(links, l => l.weight)).range([0.1, 0.5]);

    const realmColors = { Inferno: '#DC2626', Purgatorio: '#A3824A', Paradiso: '#3B82F6' };

    function nodeColor(d) {
      if (realm !== 'All') {
        // When filtering: exclusive characters get full color, cross-realm get muted
        if (d.realm_association.length === 1) return realmColors[realm];
        return d3.color(realmColors[realm]).brighter(0.5).formatHex();
      }
      // When showing all: color by primary realm (single > multi)
      if (d.realm_association.length === 1) return realmColors[d.realm_association[0]];
      if (d.realm_association.includes('Paradiso')) return '#3B82F6';
      if (d.realm_association.includes('Purgatorio')) return '#A3824A';
      return '#DC2626';
    }

    function nodeOpacity(d) {
      if (realm === 'All') return 0.85;
      // Exclusive to this realm: fully opaque; cross-realm: semi-transparent
      return d.realm_association.length === 1 ? 0.9 : 0.55;
    }

    // Force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(80).strength(0.3))
      .force('charge', d3.forceManyBody().strength(-150))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => nodeSize(d.mentions) + 5));
    currentSimulation = simulation;

    // Store refs for search/click highlighting
    currentNodes = nodes;
    currentRealm = realm;
    d3NodeSize = nodeSize;
    d3NodeColor = nodeColor;
    d3NodeOpacity = nodeOpacity;
    d3NodeStroke = d => realm !== 'All' && d.realm_association.length === 1 ? '#fff' : '#222';
    d3NodeStrokeWidth = d => realm !== 'All' && d.realm_association.length === 1 ? 1 : 1.5;
    d3LinkOpacity = linkOpacity;

    // Reset search state on redraw
    highlightedNode = null;
    searchQuery = '';

    // Draw links
    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#555')
      .attr('stroke-width', d => linkWidth(d.weight))
      .attr('stroke-opacity', d => linkOpacity(d.weight));

    d3Links = link;

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
      .attr('stroke', d => realm !== 'All' && d.realm_association.length === 1 ? '#fff' : '#222')
      .attr('stroke-width', d => realm !== 'All' && d.realm_association.length === 1 ? 1 : 1.5)
      .attr('opacity', d => nodeOpacity(d));

    d3Nodes = node;

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

    // Tooltip on hover (only when no node is actively highlighted)
    node.on('mouseenter', function(event, d) {
      if (highlightedNode) {
        // Still show tooltip but don't change graph state
        const exclusiveLabel = realm !== 'All' && d.realm_association.length === 1
          ? `<span style="color:#fff;font-size:10px;"> (exclusive to ${realm})</span>` : '';
        showTooltip(tooltip, `
          <div style="font-weight:bold;color:${nodeColor(d)};font-size:14px;">${d.id}${exclusiveLabel}</div>
          <div style="margin-top:4px;">
            <span style="color:#999">Role:</span> ${d.role}<br/>
            <span style="color:#999">Appears in:</span> ${d.mentions} cantos<br/>
            <span style="color:#999">Realms:</span> ${d.realm_association.join(', ')}<br/>
            <span style="color:#999">Significance:</span> ${d.significance || 'N/A'}
          </div>
        `, event);
        return;
      }

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

      const exclusiveLabel = realm !== 'All' && d.realm_association.length === 1
        ? `<span style="color:#fff;font-size:10px;"> (exclusive to ${realm})</span>` : '';
      showTooltip(tooltip, `
        <div style="font-weight:bold;color:${nodeColor(d)};font-size:14px;">${d.id}${exclusiveLabel}</div>
        <div style="margin-top:4px;">
          <span style="color:#999">Role:</span> ${d.role}<br/>
          <span style="color:#999">Appears in:</span> ${d.mentions} cantos<br/>
          <span style="color:#999">Realms:</span> ${d.realm_association.join(', ')}<br/>
          <span style="color:#999">Significance:</span> ${d.significance || 'N/A'}
        </div>
      `, event);
    })
    .on('mouseleave', function(event, d) {
      hideTooltip(tooltip);
      if (highlightedNode) return; // Don't reset graph during active highlight

      d3.select(this).select('circle')
        .transition().duration(150)
        .attr('r', nodeSize(d.mentions))
        .attr('stroke', d3NodeStroke(d))
        .attr('stroke-width', d3NodeStrokeWidth(d));

      link.attr('stroke-opacity', l => linkOpacity(l.weight))
        .attr('stroke', '#555');
    })
    .on('click', function(event, d) {
      event.stopPropagation();
      if (highlightedNode === d.id) {
        // Clicking same node again: deselect
        clearSearch();
      } else {
        // Select this node
        highlightedNode = d.id;
        searchQuery = d.id;
        searchFocused = false;
        highlightNodeInGraph(d.id);
      }
    });

    // Click on SVG background to deselect
    svg.on('click', function() {
      if (highlightedNode) {
        clearSearch();
      }
    });

    // Simulation tick — clamp nodes within SVG bounds
    simulation.on('tick', () => {
      nodes.forEach(d => {
        d.x = Math.max(25, Math.min(width - 25, d.x));
        d.y = Math.max(30, Math.min(height - 25, d.y));
      });
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

    // ── Legend ────────────────────────────────────────────────
    const legendPad = 14;
    const legendW = 220;
    const legendLineH = 18;
    const legendItems = [];

    // Section 1: Connections explanation
    legendItems.push({ type: 'header', text: 'Connections' });
    legendItems.push({ type: 'desc', text: 'Lines connect characters who appear' });
    legendItems.push({ type: 'desc', text: 'together in the same canto.' });
    legendItems.push({ type: 'link', text: 'Thicker line = more shared cantos', thick: true });
    legendItems.push({ type: 'link', text: 'Thinner line = fewer shared cantos', thick: false });
    legendItems.push({ type: 'spacer' });

    // Section 2: Node size
    legendItems.push({ type: 'header', text: 'Node Size' });
    legendItems.push({ type: 'size', text: 'Larger = mentioned in more cantos' });
    legendItems.push({ type: 'spacer' });

    // Section 3: Colors (only when a realm filter is active)
    if (realm !== 'All') {
      legendItems.push({ type: 'header', text: 'Colors' });
      legendItems.push({ type: 'color', text: `Exclusive to ${realm}`, color: realmColors[realm], bright: true });
      legendItems.push({ type: 'color', text: 'Also appears in other realms', color: d3.color(realmColors[realm]).brighter(0.5).formatHex(), bright: false });
    }

    const legendH = legendPad * 2 + legendItems.length * legendLineH;
    const legendX = width - legendW - 16;
    const legendY = height - legendH - 16;

    const legend = svg.append('g')
      .attr('transform', `translate(${legendX}, ${legendY})`);

    legend.append('rect')
      .attr('width', legendW).attr('height', legendH)
      .attr('rx', 6).attr('ry', 6)
      .attr('fill', 'rgba(10, 10, 15, 0.85)')
      .attr('stroke', '#333')
      .attr('stroke-width', 1);

    legendItems.forEach((item, i) => {
      const y = legendPad + i * legendLineH + 12;

      if (item.type === 'header') {
        legend.append('text')
          .attr('x', legendPad).attr('y', y)
          .attr('fill', '#ddd')
          .attr('font-size', '11px')
          .attr('font-weight', '600')
          .attr('font-family', "'EB Garamond', Georgia, serif")
          .text(item.text);
      } else if (item.type === 'desc') {
        legend.append('text')
          .attr('x', legendPad).attr('y', y)
          .attr('fill', '#888')
          .attr('font-size', '10px')
          .attr('font-family', "'EB Garamond', Georgia, serif")
          .attr('font-style', 'italic')
          .text(item.text);
      } else if (item.type === 'link') {
        legend.append('line')
          .attr('x1', legendPad).attr('y1', y - 4)
          .attr('x2', legendPad + 28).attr('y2', y - 4)
          .attr('stroke', '#888')
          .attr('stroke-width', item.thick ? 3.5 : 1)
          .attr('stroke-opacity', item.thick ? 0.6 : 0.3);
        legend.append('text')
          .attr('x', legendPad + 36).attr('y', y)
          .attr('fill', '#999')
          .attr('font-size', '10px')
          .attr('font-family', "'EB Garamond', Georgia, serif")
          .text(item.text);
      } else if (item.type === 'size') {
        legend.append('circle')
          .attr('cx', legendPad + 5).attr('cy', y - 4)
          .attr('r', 3).attr('fill', '#888');
        legend.append('circle')
          .attr('cx', legendPad + 18).attr('cy', y - 4)
          .attr('r', 6).attr('fill', '#888');
        legend.append('text')
          .attr('x', legendPad + 32).attr('y', y)
          .attr('fill', '#999')
          .attr('font-size', '10px')
          .attr('font-family', "'EB Garamond', Georgia, serif")
          .text(item.text);
      } else if (item.type === 'color') {
        legend.append('circle')
          .attr('cx', legendPad + 6).attr('cy', y - 4)
          .attr('r', 5)
          .attr('fill', item.color)
          .attr('opacity', item.bright === false ? 0.55 : 0.9)
          .attr('stroke', item.bright ? '#fff' : '#222')
          .attr('stroke-width', 1);
        legend.append('text')
          .attr('x', legendPad + 18).attr('y', y)
          .attr('fill', '#999')
          .attr('font-size', '10px')
          .attr('font-family', "'EB Garamond', Georgia, serif")
          .text(item.text);
      }
      // spacer: no rendering, just vertical gap
    });
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
  <div class="search-bar">
    <div class="search-input-wrapper">
      <svg class="search-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#666" stroke-width="2">
        <circle cx="11" cy="11" r="7"/><line x1="16.5" y1="16.5" x2="21" y2="21"/>
      </svg>
      <input
        type="text"
        class="search-input"
        placeholder="Search characters..."
        bind:value={searchQuery}
        onfocus={() => { searchFocused = true; }}
        onblur={() => { setTimeout(() => { searchFocused = false; }, 150); }}
        onkeydown={(e) => {
          if (e.key === 'Enter' && suggestions().length > 0) {
            selectCharacter(suggestions()[0]);
          }
          if (e.key === 'Escape') { clearSearch(); e.target.blur(); }
        }}
      />
      {#if searchQuery}
        <button class="clear-btn" onclick={clearSearch}>&times;</button>
      {/if}
    </div>
    {#if searchFocused && suggestions().length > 0}
      <ul class="suggestions">
        {#each suggestions() as name}
          <li>
            <button class="suggestion-btn" onmousedown={() => selectCharacter(name)}>
              {name}
            </button>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
  <div class="svg-wrapper" bind:this={svgWrapper}>
    <svg bind:this={container} {width} {height}></svg>
  </div>
</div>

<style>
  .network-container {
    width: 100%;
  }
  .svg-wrapper {
    width: 100%;
    min-height: 550px;
    height: 65vh;
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
  .search-bar {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 10px;
  }
  .search-input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
    width: 260px;
  }
  .search-icon {
    position: absolute;
    left: 10px;
    pointer-events: none;
  }
  .search-input {
    width: 100%;
    padding: 6px 28px 6px 30px;
    background: rgba(255,255,255,0.04);
    border: 1px solid #333;
    border-radius: 16px;
    color: #ddd;
    font-size: 12px;
    font-family: 'EB Garamond', Georgia, serif;
    outline: none;
    transition: border-color 0.2s;
  }
  .search-input::placeholder {
    color: #555;
  }
  .search-input:focus {
    border-color: #666;
    background: rgba(255,255,255,0.06);
  }
  .clear-btn {
    position: absolute;
    right: 6px;
    background: none;
    border: none;
    color: #888;
    font-size: 16px;
    cursor: pointer;
    padding: 0 4px;
    line-height: 1;
  }
  .clear-btn:hover {
    color: #fff;
  }
  .suggestions {
    position: absolute;
    top: 100%;
    width: 260px;
    margin: 4px 0 0;
    padding: 4px 0;
    list-style: none;
    background: rgba(20, 20, 28, 0.95);
    border: 1px solid #333;
    border-radius: 8px;
    z-index: 10;
    backdrop-filter: blur(8px);
  }
  .suggestion-btn {
    display: block;
    width: 100%;
    padding: 5px 14px;
    text-align: left;
    background: none;
    border: none;
    color: #ccc;
    font-size: 12px;
    font-family: 'EB Garamond', Georgia, serif;
    cursor: pointer;
  }
  .suggestion-btn:hover {
    background: rgba(255,255,255,0.08);
    color: #fff;
  }
  svg {
    display: block;
    overflow: visible;
  }
</style>
