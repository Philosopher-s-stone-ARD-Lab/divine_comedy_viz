# Divine Comedy Data Visualization Project - Context for Claude Code

## Project Overview
Create an interactive data visualization of Dante's Divine Comedy using a Data Visualization Journey approach. The project extracts structured data from the text, performs analysis, and creates beautiful visualizations using D3.js and Svelte.

## Source Material
- **File**: `divine-comedy.pdf`
- **Translation**: Longfellow translation
- **Structure**: 3 realms (Inferno, Purgatorio, Paradiso), 100 cantos total

## Tasks

### 1. Environment Setup
- Create a Python virtual environment for text processing
- Install required libraries: `pdfplumber` or `pypdf`, `nltk`, `pandas`, `json`
- Set up a Svelte project with D3.js integration
- Create a comprehensive README with setup and run instructions

### 2. PDF Text Extraction & Parsing
Extract and parse `divine-comedy.pdf` to identify:
- **Structural elements**: Realms (Inferno/Purgatorio/Paradiso), Cantos, Lines
- **Character mentions**: Names of souls, mythological figures, historical persons
- **Location markers**: Circle numbers, terrace numbers, sphere numbers, geographic references
- **Quotes**: Notable passages and dialogue
- **Structural patterns**: Canto beginnings/endings, section divisions

Use regex patterns to identify:
- Canto headers (e.g., "CANTO I", "CANTO II", etc.)
- Character name patterns (capitalized names, historical figures)
- Location keywords (Circle, Terrace, Sphere, Hell, Purgatory, Paradise)

### 3. Create Structured JSON Dataset
Generate a comprehensive JSON file (`divine-comedy-data.json`) with this structure:

```json
{
  "metadata": {
    "title": "Divine Comedy",
    "author": "Dante Alighieri",
    "translator": "Henry Wadsworth Longfellow",
    "total_cantos": 100,
    "structure": "3 realms, 100 cantos"
  },
  "realms": [
    {
      "name": "Inferno",
      "description": "The descent through Hell",
      "canto_count": 34,
      "cantos": [
        {
          "number": 1,
          "title": "Canto I",
          "realm": "Inferno",
          "location": "Dark Wood",
          "line_count": 0,
          "characters": [],
          "key_themes": [],
          "notable_quotes": [],
          "sentiment_score": 0.0,
          "word_count": 0,
          "top_words": []
        }
      ],
      "divisions": [
        {
          "circle": 1,
          "name": "Limbo",
          "canto_range": [4, 4],
          "souls_mentioned": [],
          "sin_category": null,
          "punishment": "Eternal longing without hope",
          "symbolism": ["Neutrality", "Unbaptized virtuous pagans"],
          "notable_characters": []
        }
      ]
    }
  ],
  "characters": [
    {
      "name": "Virgil",
      "role": "Guide",
      "appearances": [],
      "realm_association": ["Inferno", "Purgatorio"],
      "significance": "Dante's guide through Hell and Purgatory"
    }
  ],
  "themes": [
    {
      "name": "Justice",
      "frequency": 0,
      "realms": [],
      "description": "Divine justice and retribution"
    }
  ]
}
```

### 4. Text Analysis with NLTK
Perform the following analyses and include results in the JSON:

**Sentiment Analysis**:
- Sentiment score per canto (using NLTK's VADER or TextBlob)
- Emotional arc across the journey (should show progression from dark to light)
- Identify emotional peaks and valleys

**Frequency Analysis**:
- Top 20 most frequent words (excluding stop words) per realm
- Top 10 words per canto
- Key thematic words: love, light, dark, pain, sin, virtue, heaven, hell, etc.
- Character name frequency and distribution

**Pattern Analysis with Regex**:
- Count tercets (terza rima stanzas)
- Identify recurring phrases
- Extract direct speech/dialogue
- Find religious references (God, Christ, Virgin Mary, Satan, etc.)
- Identify classical references (Homer, Virgil, Caesar, etc.)

**Statistical Metrics**:
- Average line count per canto
- Word count distribution across realms
- Vocabulary richness (unique words per realm)
- Reading complexity metrics

### 5. Additional Data Enrichment
Create supplementary datasets:

**Network Data** (`network-data.json`):
- Character co-occurrence matrix
- Character relationships and interactions
- Guide-soul relationships

**Journey Data** (`journey-data.json`):
- Spatial progression coordinates (for visualization)
- Descent/ascent metrics
- Temporal markers in the narrative

**Symbolic Data** (`symbols-data.json`):
- Rivers (Acheron, Styx, Lethe, etc.)
- Beasts and creatures
- Celestial bodies
- Numbers and their significance (3, 9, 10, etc.)

### 6. D3.js & Svelte Visualization Setup
Create a Svelte application with multiple visualization components:

**Project Structure**:
```
/divine-comedy-viz
  /src
    /components
      - SpiralJourney.svelte (main spiral descent/ascent viz)
      - NetworkGraph.svelte (character relationships)
      - SentimentFlow.svelte (emotional arc over time)
      - ThemeRadial.svelte (radial chart of themes)
      - CantoExplorer.svelte (detailed canto view)
    /data
      - divine-comedy-data.json
      - network-data.json
      - journey-data.json
      - symbols-data.json
    /utils
      - dataProcessing.js
      - d3Helpers.js
    App.svelte
    main.js
  /public
  package.json
  README.md
```

**Visualization Components to Create**:

1. **Spiral Journey Visualization**:
   - 3D spiral descending (Inferno), horizontal (Purgatorio), ascending (Paradiso)
   - Each canto as a node with size based on word count
   - Color gradient from dark (Inferno) to light (Paradiso)
   - Interactive: hover for canto details, click to expand

2. **Sentiment Flow Chart**:
   - Line chart showing emotional progression
   - X-axis: canto sequence (1-100)
   - Y-axis: sentiment score
   - Area chart showing intensity

3. **Character Network Graph**:
   - Force-directed graph of character relationships
   - Node size: frequency of mentions
   - Edges: co-occurrences in same cantos
   - Color by realm association

4. **Thematic Radial Chart**:
   - Circular layout with themes as spokes
   - Frequency shown as radius
   - Interactive filtering by realm

5. **Word Cloud / Frequency Visualization**:
   - Animated word cloud per realm
   - Size based on frequency
   - Transition between realms

**Visual Design Principles**:
- **Color Palette**:
  - Inferno: deep reds, oranges, dark purples (#8B0000, #FF4500, #4B0082)
  - Purgatorio: earth tones, grays, muted greens (#8B7355, #696969, #556B2F)
  - Paradiso: celestial blues, golds, whites (#1E90FF, #FFD700, #F0F8FF)
- **Typography**: Elegant serif fonts (Crimson Text, EB Garamond)
- **Animations**: Smooth transitions using D3 transitions and Svelte animations
- **Interactivity**: Tooltips, zoom, pan, filtering

### 7. Technical Requirements

**Python Environment**:
- Python 3.8+
- Libraries: pdfplumber, nltk, pandas, numpy, json, re

**Svelte/JavaScript Environment**:
- Node.js 16+
- Svelte 4
- D3.js v7
- Additional: d3-force, d3-scale, d3-shape, d3-transition

**Development Workflow**:
1. Extract and analyze PDF → Generate JSON datasets
2. Set up Svelte project with D3.js
3. Create individual visualization components
4. Integrate all components into main app
5. Add interactivity and transitions
6. Polish UI/UX

### 8. Deliverables

**Files to Create**:
- `extract_and_analyze.py` - Main Python script for PDF processing and analysis
- `divine-comedy-data.json` - Complete structured dataset
- `network-data.json` - Character network data
- `journey-data.json` - Spatial/temporal journey data
- `symbols-data.json` - Symbolic elements
- `analysis-report.md` - Summary of findings from text analysis
- Complete Svelte application with all visualization components
- `README.md` - Comprehensive setup and run instructions
- `requirements.txt` - Python dependencies
- `package.json` - Node.js dependencies

**README Should Include**:
- Project overview and goals
- Prerequisites (Python, Node.js versions)
- Setup instructions for both Python and Svelte environments
- How to run the data extraction and analysis
- How to run the visualization app
- Project structure explanation
- Future enhancement ideas
- Credits and sources

### 9. Important Notes

**For the Coding Assistant**:
- Use a Python virtual environment (venv) for isolation
- Handle PDF parsing errors gracefully (some PDFs have formatting issues)
- NLTK may require downloading additional data (`nltk.download('vader_lexicon')`, etc.)
- Focus on extractable, objective data first (structure, characters, word counts)
- Leave placeholders for interpretive data (sin classifications, symbolism) that require human review
- Add comments indicating where manual enrichment is recommended
- Make the JSON structure extensible for future additions
- Ensure all visualizations are responsive
- Add loading states for data fetching
- Include error boundaries in Svelte components

**Data Accuracy**:
- Cross-reference extracted character names against known lists
- Validate canto counts (should be 34, 33, 33)
- Check for parsing errors in PDF extraction
- Include data validation scripts

**Performance Considerations**:
- Optimize D3 rendering for large datasets
- Use Svelte's reactivity efficiently
- Consider virtualization for long lists
- Lazy load visualization components

## Expected Outcome
A fully functional, beautiful data visualization web application that allows users to explore Dante's Divine Comedy through multiple interactive visual lenses, revealing patterns, themes, and structures in the text that aren't immediately apparent from reading alone.
