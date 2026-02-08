<script>
  import { onMount } from 'svelte';
  import SpiralJourney from './components/SpiralJourney.svelte';
  import SentimentFlow from './components/SentimentFlow.svelte';
  import NetworkGraph from './components/NetworkGraph.svelte';
  import ThemeRadial from './components/ThemeRadial.svelte';
  import CantoExplorer from './components/CantoExplorer.svelte';

  import mainDataJson from './data/divine-comedy-data.json';
  import networkDataJson from './data/network-data.json';
  import journeyDataJson from './data/journey-data.json';
  import symbolsDataJson from './data/symbols-data.json';

  let mainData = $state(null);
  let networkData = $state(null);
  let journeyData = $state([]);
  let symbolsData = $state(null);
  let allCantos = $state([]);
  let loading = $state(true);
  let selectedCanto = $state(null);
  let activeSection = $state('spiral');

  const sections = [
    { id: 'spiral', label: 'Journey', icon: '&#10042;' },
    { id: 'sentiment', label: 'Emotion', icon: '&#9829;' },
    { id: 'network', label: 'Characters', icon: '&#9733;' },
    { id: 'themes', label: 'Themes', icon: '&#9673;' },
    { id: 'explorer', label: 'Explorer', icon: '&#9776;' },
  ];

  onMount(() => {
    mainData = mainDataJson;
    networkData = networkDataJson;
    journeyData = journeyDataJson.journey || [];
    symbolsData = symbolsDataJson;
    allCantos = mainData.realms.flatMap(r => r.cantos);
    loading = false;
  });

  function handleCantoSelect(globalNumber) {
    selectedCanto = globalNumber;
    if (activeSection !== 'explorer') {
      activeSection = 'explorer';
    }
  }

  // Stats for hero section
  const stats = $derived(mainData ? {
    totalCantos: mainData.metadata.total_cantos,
    totalWords: mainData.realms.reduce((sum, r) => sum + r.total_words, 0),
    totalCharacters: mainData.characters.length,
    totalThemes: mainData.themes.length,
  } : null);
</script>

<div class="app">
  {#if loading}
    <div class="loading">
      <div class="loading-spinner"></div>
      <p>Loading the Divine Comedy...</p>
    </div>
  {:else}
    <!-- Hero Header -->
    <header class="hero">
      <div class="hero-bg"></div>
      <div class="hero-content">
        <h1 class="title">The Divine Comedy</h1>
        <p class="subtitle">A Data Visualization Journey through Dante Alighieri's Masterpiece</p>
        <p class="translator">Longfellow Translation</p>
        {#if stats}
          <div class="hero-stats">
            <div class="hero-stat">
              <span class="hero-stat-value">{stats.totalCantos}</span>
              <span class="hero-stat-label">Cantos</span>
            </div>
            <div class="hero-stat">
              <span class="hero-stat-value">{stats.totalWords.toLocaleString()}</span>
              <span class="hero-stat-label">Words</span>
            </div>
            <div class="hero-stat">
              <span class="hero-stat-value">{stats.totalCharacters}</span>
              <span class="hero-stat-label">Characters</span>
            </div>
            <div class="hero-stat">
              <span class="hero-stat-value">{stats.totalThemes}</span>
              <span class="hero-stat-label">Themes</span>
            </div>
          </div>
        {/if}
        <!-- Realm summary -->
        <div class="realm-summary">
          {#each mainData.realms as realm}
            <div class="realm-card" style="border-color: {realm.name === 'Inferno' ? '#DC2626' : realm.name === 'Purgatorio' ? '#A3824A' : '#3B82F6'}">
              <h3 style="color: {realm.name === 'Inferno' ? '#DC2626' : realm.name === 'Purgatorio' ? '#A3824A' : '#3B82F6'}">{realm.name}</h3>
              <p>{realm.canto_count} cantos &middot; {realm.total_words.toLocaleString()} words</p>
              <p class="realm-desc">{realm.description}</p>
            </div>
          {/each}
        </div>
      </div>
    </header>

    <!-- Navigation -->
    <nav class="nav-bar">
      {#each sections as sec}
        <button
          class="nav-btn"
          class:active={activeSection === sec.id}
          onclick={() => { activeSection = sec.id; }}
        >
          <span class="nav-icon">{@html sec.icon}</span>
          <span class="nav-label">{sec.label}</span>
        </button>
      {/each}
    </nav>

    <!-- Visualization Sections -->
    <main class="main-content">
      {#if activeSection === 'spiral'}
        <section class="viz-section">
          <SpiralJourney
            {journeyData}
            {mainData}
            onCantoSelect={handleCantoSelect}
          />
        </section>
      {:else if activeSection === 'sentiment'}
        <section class="viz-section">
          <SentimentFlow
            cantos={allCantos}
            onCantoSelect={handleCantoSelect}
          />
        </section>
      {:else if activeSection === 'network'}
        <section class="viz-section">
          <NetworkGraph
            {networkData}
            onCantoSelect={handleCantoSelect}
          />
        </section>
      {:else if activeSection === 'themes'}
        <section class="viz-section">
          <ThemeRadial
            themes={mainData.themes}
            realmThemes={{}}
          />
        </section>
      {:else if activeSection === 'explorer'}
        <section class="viz-section">
          <CantoExplorer
            cantos={allCantos}
            bind:selectedCanto
          />
        </section>
      {/if}
    </main>

    <!-- Footer -->
    <footer class="footer">
      <p>Divine Comedy Data Visualization &middot; Data extracted from Longfellow translation</p>
      <p class="footer-note">Built with Svelte & D3.js</p>
    </footer>
  {/if}
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    background: #0a0a0f;
    color: #e0e0e0;
    font-family: 'EB Garamond', 'Crimson Text', Georgia, 'Times New Roman', serif;
    -webkit-font-smoothing: antialiased;
  }

  :global(*) {
    box-sizing: border-box;
  }

  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Loading */
  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    gap: 16px;
    color: #888;
  }
  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 2px solid #333;
    border-top-color: #FFD700;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Hero */
  .hero {
    position: relative;
    padding: 60px 24px 40px;
    text-align: center;
    overflow: hidden;
  }
  .hero-bg {
    position: absolute;
    inset: 0;
    background:
      radial-gradient(ellipse at 20% 50%, rgba(139, 0, 0, 0.12) 0%, transparent 50%),
      radial-gradient(ellipse at 50% 50%, rgba(139, 115, 85, 0.08) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 50%, rgba(30, 144, 255, 0.12) 0%, transparent 50%);
    pointer-events: none;
  }
  .hero-content {
    position: relative;
    max-width: 900px;
    margin: 0 auto;
  }
  .title {
    font-size: 48px;
    font-weight: 400;
    margin: 0;
    letter-spacing: 3px;
    background: linear-gradient(135deg, #DC2626 0%, #FFD700 50%, #3B82F6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .subtitle {
    font-size: 18px;
    color: #999;
    margin: 8px 0 4px;
    font-style: italic;
  }
  .translator {
    font-size: 13px;
    color: #666;
    margin: 0 0 28px;
  }

  .hero-stats {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-bottom: 30px;
  }
  .hero-stat {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .hero-stat-value {
    font-size: 28px;
    font-weight: bold;
    color: #e0e0e0;
  }
  .hero-stat-label {
    font-size: 12px;
    color: #777;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .realm-summary {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    max-width: 700px;
    margin: 0 auto;
  }
  .realm-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid #2a2a2a;
    border-top: 3px solid;
    border-radius: 8px;
    padding: 16px;
    text-align: left;
  }
  .realm-card h3 {
    margin: 0 0 6px;
    font-size: 16px;
    font-weight: 600;
  }
  .realm-card p {
    margin: 0;
    font-size: 12px;
    color: #888;
  }
  .realm-desc {
    margin-top: 6px !important;
    font-style: italic;
    color: #666 !important;
  }

  /* Nav */
  .nav-bar {
    display: flex;
    justify-content: center;
    gap: 4px;
    padding: 12px 24px;
    background: rgba(10, 10, 15, 0.95);
    border-top: 1px solid #1a1a1f;
    border-bottom: 1px solid #1a1a1f;
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(10px);
  }
  .nav-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 20px;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 20px;
    color: #888;
    cursor: pointer;
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 14px;
    transition: all 0.2s;
  }
  .nav-btn:hover {
    color: #ccc;
    border-color: #333;
  }
  .nav-btn.active {
    color: #fff;
    background: rgba(255,255,255,0.06);
    border-color: #444;
  }
  .nav-icon {
    font-size: 16px;
  }

  /* Main */
  .main-content {
    flex: 1;
    padding: 30px 24px;
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
  }
  .viz-section {
    min-height: 400px;
  }

  /* Footer */
  .footer {
    text-align: center;
    padding: 24px;
    border-top: 1px solid #1a1a1f;
    color: #555;
    font-size: 12px;
  }
  .footer p { margin: 2px 0; }
  .footer-note { color: #444; }

  @media (max-width: 768px) {
    .title { font-size: 32px; }
    .hero-stats { gap: 20px; }
    .hero-stat-value { font-size: 22px; }
    .realm-summary { grid-template-columns: 1fr; }
    .nav-bar { overflow-x: auto; justify-content: flex-start; }
    .nav-label { display: none; }
  }
</style>
