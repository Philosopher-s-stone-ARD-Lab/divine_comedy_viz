<script>
  import * as d3 from 'd3';
  import { getRealmColor, getCantoColor } from '../utils/dataProcessing.js';
  import { journeyColorScale } from '../utils/d3Helpers.js';

  let { cantos = [], selectedCanto = $bindable(null) } = $props();

  let searchTerm = $state('');

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

  const activeCanto = $derived(
    selectedCanto ? cantos.find(c => c.global_number === selectedCanto) : null
  );

  function sentimentBar(value) {
    const pct = ((value + 1) / 2) * 100;
    return `linear-gradient(to right, #8B0000 0%, #FF4500 25%, #888 50%, #556B2F 75%, #FFD700 100%)`;
  }

  function sentimentLabel(value) {
    if (value > 0.5) return 'Very Positive';
    if (value > 0.15) return 'Positive';
    if (value > -0.15) return 'Neutral';
    if (value > -0.5) return 'Negative';
    return 'Very Negative';
  }
</script>

<div class="explorer">
  <div class="explorer-sidebar">
    <div class="search-box">
      <input
        type="text"
        placeholder="Search cantos, characters, locations..."
        bind:value={searchTerm}
      />
    </div>
    <div class="canto-list">
      {#each filteredCantos as canto (canto.global_number)}
        <button
          class="canto-item"
          class:active={selectedCanto === canto.global_number}
          style="border-left: 3px solid {getCantoColor(canto.global_number)}"
          onclick={() => { selectedCanto = canto.global_number; }}
        >
          <span class="canto-num">{canto.global_number}</span>
          <span class="canto-info">
            <span class="canto-title">{canto.realm}: {canto.title}</span>
            <span class="canto-location">{canto.location}</span>
          </span>
        </button>
      {/each}
    </div>
  </div>

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
          <div class="stat-value" style="color: {activeCanto.sentiment.compound > 0.15 ? '#10B981' : activeCanto.sentiment.compound < -0.15 ? '#EF4444' : '#888'}">
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
    display: grid;
    grid-template-columns: 280px 1fr;
    gap: 20px;
    min-height: 500px;
    max-height: 700px;
  }
  .explorer-sidebar {
    display: flex;
    flex-direction: column;
    gap: 10px;
    overflow: hidden;
  }
  .search-box input {
    width: 100%;
    padding: 8px 12px;
    background: rgba(255,255,255,0.05);
    border: 1px solid #333;
    border-radius: 8px;
    color: #ccc;
    font-size: 13px;
    font-family: 'EB Garamond', Georgia, serif;
    box-sizing: border-box;
  }
  .search-box input::placeholder { color: #666; }
  .search-box input:focus { outline: none; border-color: #666; }
  .canto-list {
    overflow-y: auto;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .canto-list::-webkit-scrollbar { width: 4px; }
  .canto-list::-webkit-scrollbar-track { background: transparent; }
  .canto-list::-webkit-scrollbar-thumb { background: #444; border-radius: 2px; }
  .canto-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    background: transparent;
    border: none;
    color: #aaa;
    cursor: pointer;
    text-align: left;
    font-family: 'EB Garamond', Georgia, serif;
    transition: background 0.15s;
    border-radius: 4px;
  }
  .canto-item:hover { background: rgba(255,255,255,0.05); }
  .canto-item.active { background: rgba(255,255,255,0.1); color: #fff; }
  .canto-num {
    font-size: 11px;
    color: #666;
    width: 24px;
    text-align: right;
    flex-shrink: 0;
  }
  .canto-info { display: flex; flex-direction: column; }
  .canto-title { font-size: 12px; }
  .canto-location { font-size: 10px; color: #666; }

  .explorer-detail {
    overflow-y: auto;
    padding-right: 10px;
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
    height: 100%;
    color: #666;
    font-family: 'EB Garamond', Georgia, serif;
    text-align: center;
  }
  .detail-empty p { margin: 4px 0; }
  .hint { font-size: 12px; color: #555; }

  @media (max-width: 768px) {
    .explorer {
      grid-template-columns: 1fr;
      max-height: none;
    }
    .explorer-sidebar {
      max-height: 250px;
    }
  }
</style>
