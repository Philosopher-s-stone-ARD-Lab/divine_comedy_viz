<script>
  import * as d3 from 'd3';
  import { getRealmColor, getCantoColor } from '../utils/dataProcessing.js';
  import { journeyColorScale } from '../utils/d3Helpers.js';

  let { cantos = [], selectedCanto = $bindable(null) } = $props();

  let searchTerm = $state('');
  let dropdownOpen = $state(false);
  let expandedRealms = $state({ Inferno: true, Purgatorio: false, Paradiso: false });

  const filteredCantos = $derived(
    searchTerm
      ? cantos.filter(c =>
          c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.realm.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.characters?.some(ch => ch.name.toLowerCase().includes(searchTerm.toLowerCase()))
        )
      : cantos
  );

  const groupedCantos = $derived.by(() => {
    const groups = {};
    for (const c of filteredCantos) {
      if (!groups[c.realm]) groups[c.realm] = [];
      groups[c.realm].push(c);
    }
    return groups;
  });

  const realmOrder = ['Inferno', 'Purgatorio', 'Paradiso'];

  const activeCanto = $derived(
    selectedCanto ? cantos.find(c => c.global_number === selectedCanto) : null
  );

  // Auto-expand the realm of the selected canto
  $effect(() => {
    if (activeCanto) {
      expandedRealms[activeCanto.realm] = true;
    }
  });

  // When searching, expand all realms that have results
  $effect(() => {
    if (searchTerm) {
      const groups = groupedCantos;
      for (const realm of realmOrder) {
        expandedRealms[realm] = !!groups[realm]?.length;
      }
    }
  });

  function toggleRealm(realm) {
    expandedRealms[realm] = !expandedRealms[realm];
  }

  function selectCanto(globalNumber) {
    selectedCanto = globalNumber;
    dropdownOpen = false;
  }

  function sentimentBar(value) {
    const pct = ((value + 1) / 2) * 100;
    return `linear-gradient(to right, #8B0000 0%, #FF4500 25%, #888 50%, #556B2F 75%, #FFD700 100%)`;
  }

  function sentimentLabel(value) {
    if (value > 0.4) return 'Very Positive';
    if (value > 0.1) return 'Positive';
    if (value > -0.1) return 'Neutral';
    if (value > -0.4) return 'Negative';
    return 'Very Negative';
  }
</script>

<div class="explorer">
  <!-- Dropdown selector -->
  <div class="canto-selector">
    <button class="selector-trigger" onclick={() => { dropdownOpen = !dropdownOpen; }}>
      {#if activeCanto}
        <span class="trigger-color" style="background: {getCantoColor(activeCanto.global_number)}"></span>
        <span class="trigger-label">{activeCanto.realm}: {activeCanto.title}</span>
        <span class="trigger-location">{activeCanto.location}</span>
      {:else}
        <span class="trigger-label placeholder">Select a canto...</span>
      {/if}
      <span class="trigger-arrow">{dropdownOpen ? '\u25B4' : '\u25BE'}</span>
    </button>

    {#if dropdownOpen}
      <button class="dropdown-backdrop" tabindex="-1" onclick={() => { dropdownOpen = false; }}></button>
      <div class="dropdown-panel">
        <div class="dropdown-search">
          <input
            type="text"
            placeholder="Search cantos, characters, locations..."
            bind:value={searchTerm}
          />
        </div>
        <div class="dropdown-list">
          {#each realmOrder as realm}
            {@const realmCantos = groupedCantos[realm] || []}
            {#if realmCantos.length > 0}
              <div class="realm-group">
                <button
                  class="realm-header"
                  class:expanded={expandedRealms[realm]}
                  onclick={() => toggleRealm(realm)}
                >
                  <span class="realm-arrow">{expandedRealms[realm] ? '\u25BE' : '\u25B8'}</span>
                  <span class="realm-name">{realm}</span>
                  <span class="realm-count">{realmCantos.length}</span>
                </button>
                {#if expandedRealms[realm]}
                  <div class="realm-cantos">
                    {#each realmCantos as canto (canto.global_number)}
                      <button
                        class="canto-item"
                        class:active={selectedCanto === canto.global_number}
                        style="border-left: 3px solid {getCantoColor(canto.global_number)}"
                        onclick={() => selectCanto(canto.global_number)}
                      >
                        <span class="canto-num">{canto.global_number}</span>
                        <span class="canto-info">
                          <span class="canto-title">{canto.title}</span>
                          <span class="canto-location">{canto.location}</span>
                        </span>
                      </button>
                    {/each}
                  </div>
                {/if}
              </div>
            {/if}
          {/each}
        </div>
      </div>
    {/if}
  </div>

  <!-- Detail view -->
  <div class="explorer-detail">
    {#if activeCanto}
      <div class="detail-header" style="border-bottom-color: {getCantoColor(activeCanto.global_number)}">
        <h2 style="color: {getCantoColor(activeCanto.global_number)}">
          {activeCanto.realm}: {activeCanto.title}
        </h2>
        <p class="detail-location">{activeCanto.location}</p>
      </div>

      <div class="detail-grid">
        <div class="stat-card">
          <div class="stat-label">Words</div>
          <div class="stat-value">{activeCanto.word_count.toLocaleString()}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Lines</div>
          <div class="stat-value">{activeCanto.line_count}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Vocabulary Richness</div>
          <div class="stat-value">{(activeCanto.vocabulary_richness * 100).toFixed(1)}%</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Sentiment</div>
          <div class="stat-value" style="color: {activeCanto.sentiment.compound > 0.1 ? '#10B981' : activeCanto.sentiment.compound < -0.1 ? '#EF4444' : '#888'}">
            {sentimentLabel(activeCanto.sentiment.compound)}
            <span class="stat-sub">({activeCanto.sentiment.compound.toFixed(3)})</span>
          </div>
        </div>
      </div>

      <!-- Sentiment bar -->
      <div class="section">
        <h3>Sentiment Breakdown</h3>
        <div class="sentiment-bars">
          <div class="bar-row">
            <span class="bar-label" style="color:#EF4444">Negative</span>
            <div class="bar-track">
              <div class="bar-fill" style="width: {activeCanto.sentiment.negative * 100}%; background: #EF4444;"></div>
            </div>
            <span class="bar-value">{(activeCanto.sentiment.negative * 100).toFixed(1)}%</span>
          </div>
          <div class="bar-row">
            <span class="bar-label" style="color:#888">Neutral</span>
            <div class="bar-track">
              <div class="bar-fill" style="width: {activeCanto.sentiment.neutral * 100}%; background: #666;"></div>
            </div>
            <span class="bar-value">{(activeCanto.sentiment.neutral * 100).toFixed(1)}%</span>
          </div>
          <div class="bar-row">
            <span class="bar-label" style="color:#10B981">Positive</span>
            <div class="bar-track">
              <div class="bar-fill" style="width: {activeCanto.sentiment.positive * 100}%; background: #10B981;"></div>
            </div>
            <span class="bar-value">{(activeCanto.sentiment.positive * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>

      <!-- Characters -->
      {#if activeCanto.characters?.length}
        <div class="section">
          <h3>Characters</h3>
          <div class="tag-list">
            {#each activeCanto.characters as char}
              <span class="tag character-tag">
                {char.name}
                <span class="tag-count">{char.count}</span>
              </span>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Themes -->
      {#if activeCanto.key_themes?.length}
        <div class="section">
          <h3>Key Themes</h3>
          <div class="tag-list">
            {#each activeCanto.key_themes as theme}
              <span class="tag theme-tag">
                {theme.theme}
                <span class="tag-count">{theme.count}</span>
              </span>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Top Words -->
      {#if activeCanto.top_words?.length}
        <div class="section">
          <h3>Top Words</h3>
          <div class="word-bars">
            {#each activeCanto.top_words as word, i}
              {@const maxCount = activeCanto.top_words[0]?.count || 1}
              <div class="word-row">
                <span class="word-text">{word.word}</span>
                <div class="word-bar-track">
                  <div
                    class="word-bar-fill"
                    style="width: {(word.count / maxCount) * 100}%; background: {getCantoColor(activeCanto.global_number)}; opacity: {1 - i * 0.07};"
                  ></div>
                </div>
                <span class="word-count">{word.count}</span>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Quotes -->
      {#if activeCanto.notable_quotes?.length}
        <div class="section">
          <h3>Notable Passages</h3>
          {#each activeCanto.notable_quotes as quote}
            <blockquote class="quote">{quote}</blockquote>
          {/each}
        </div>
      {/if}
    {:else}
      <div class="detail-empty">
        <p>Select a canto to explore its details</p>
        <p class="hint">Click on any canto in the list or on a node in the spiral visualization</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .explorer {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  /* ── Dropdown selector ── */
  .canto-selector {
    position: relative;
  }
  .selector-trigger {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 10px 14px;
    background: rgba(255,255,255,0.05);
    border: 1px solid #333;
    border-radius: 8px;
    color: #ccc;
    cursor: pointer;
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 14px;
    text-align: left;
    transition: border-color 0.15s;
  }
  .selector-trigger:hover { border-color: #555; }
  .trigger-color {
    width: 4px;
    height: 20px;
    border-radius: 2px;
    flex-shrink: 0;
  }
  .trigger-label { flex: 1; color: #e0e0e0; }
  .trigger-label.placeholder { color: #666; }
  .trigger-location { font-size: 12px; color: #666; }
  .trigger-arrow { font-size: 10px; color: #666; flex-shrink: 0; }

  .dropdown-backdrop {
    position: fixed;
    inset: 0;
    z-index: 9;
    background: transparent;
    border: none;
    padding: 0;
    margin: 0;
    cursor: default;
  }
  .dropdown-panel {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    max-height: 360px;
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    z-index: 10;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  .dropdown-search {
    padding: 8px;
    border-bottom: 1px solid #2a2a2a;
  }
  .dropdown-search input {
    width: 100%;
    padding: 6px 10px;
    background: rgba(255,255,255,0.05);
    border: 1px solid #333;
    border-radius: 6px;
    color: #ccc;
    font-size: 12px;
    font-family: 'EB Garamond', Georgia, serif;
    box-sizing: border-box;
  }
  .dropdown-search input::placeholder { color: #555; }
  .dropdown-search input:focus { outline: none; border-color: #555; }
  .dropdown-list {
    overflow-y: auto;
    padding: 4px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .dropdown-list::-webkit-scrollbar { width: 4px; }
  .dropdown-list::-webkit-scrollbar-track { background: transparent; }
  .dropdown-list::-webkit-scrollbar-thumb { background: #444; border-radius: 2px; }

  /* ── Realm groups inside dropdown ── */
  .realm-group { margin-bottom: 2px; }
  .realm-header {
    display: flex;
    align-items: center;
    gap: 6px;
    width: 100%;
    padding: 6px 8px;
    background: rgba(255,255,255,0.03);
    border: none;
    border-radius: 4px;
    color: #ccc;
    cursor: pointer;
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    transition: background 0.15s;
  }
  .realm-header:hover { background: rgba(255,255,255,0.07); }
  .realm-header.expanded { color: #e0e0e0; }
  .realm-arrow { font-size: 9px; width: 10px; color: #666; flex-shrink: 0; }
  .realm-name { flex: 1; text-align: left; }
  .realm-count {
    font-size: 10px;
    color: #555;
    font-weight: normal;
    background: rgba(255,255,255,0.05);
    padding: 1px 6px;
    border-radius: 8px;
  }
  .realm-cantos {
    display: flex;
    flex-direction: column;
    gap: 1px;
    padding-left: 4px;
  }

  .canto-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 8px;
    background: transparent;
    border: none;
    color: #aaa;
    cursor: pointer;
    text-align: left;
    font-family: 'EB Garamond', Georgia, serif;
    transition: background 0.15s;
    border-radius: 4px;
  }
  .canto-item:hover { background: rgba(255,255,255,0.07); }
  .canto-item.active { background: rgba(255,255,255,0.1); color: #fff; }
  .canto-num {
    font-size: 10px;
    color: #666;
    width: 20px;
    text-align: right;
    flex-shrink: 0;
  }
  .canto-info { display: flex; flex-direction: column; }
  .canto-title { font-size: 12px; }
  .canto-location { font-size: 10px; color: #555; }

  /* ── Detail panel ── */
  .explorer-detail {
    overflow-y: auto;
  }
  .detail-header {
    border-bottom: 2px solid #444;
    padding-bottom: 12px;
    margin-bottom: 16px;
  }
  .detail-header h2 {
    margin: 0;
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 22px;
  }
  .detail-location {
    color: #888;
    margin: 4px 0 0;
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 14px;
  }

  .detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
  }
  .stat-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 12px;
    text-align: center;
  }
  .stat-label { font-size: 11px; color: #888; margin-bottom: 4px; }
  .stat-value { font-size: 18px; font-weight: bold; color: #e0e0e0; font-family: 'EB Garamond', Georgia, serif; }
  .stat-sub { font-size: 12px; color: #888; font-weight: normal; }

  .section { margin-bottom: 20px; }
  .section h3 {
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 14px;
    color: #999;
    margin: 0 0 8px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .sentiment-bars { display: flex; flex-direction: column; gap: 6px; }
  .bar-row { display: flex; align-items: center; gap: 8px; }
  .bar-label { font-size: 11px; width: 60px; text-align: right; }
  .bar-track { flex: 1; height: 8px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 4px; transition: width 0.4s ease; }
  .bar-value { font-size: 11px; color: #888; width: 40px; }

  .tag-list { display: flex; flex-wrap: wrap; gap: 6px; }
  .tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-family: 'EB Garamond', Georgia, serif;
  }
  .character-tag { background: rgba(59, 130, 246, 0.15); color: #93C5FD; }
  .theme-tag { background: rgba(245, 158, 11, 0.15); color: #FCD34D; }
  .tag-count { font-size: 10px; color: #888; }

  .word-bars { display: flex; flex-direction: column; gap: 4px; }
  .word-row { display: flex; align-items: center; gap: 8px; }
  .word-text { font-size: 12px; color: #ccc; width: 70px; text-align: right; font-family: 'EB Garamond', Georgia, serif; }
  .word-bar-track { flex: 1; height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden; }
  .word-bar-fill { height: 100%; border-radius: 3px; transition: width 0.4s ease; }
  .word-count { font-size: 11px; color: #666; width: 25px; }

  .quote {
    border-left: 2px solid #555;
    padding: 6px 12px;
    margin: 8px 0;
    color: #bbb;
    font-style: italic;
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 13px;
    line-height: 1.6;
  }

  .detail-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 200px;
    color: #666;
    font-family: 'EB Garamond', Georgia, serif;
    text-align: center;
  }
  .detail-empty p { margin: 4px 0; }
  .hint { font-size: 12px; color: #555; }
</style>
