# The Divine Comedy - Interactive Data Visualization

An interactive data visualization of Dante's *Divine Comedy* (Longfellow translation) that reveals hidden patterns, themes, and structures in the text through multiple visual lenses.

## Features

- **Spiral Journey** - A spiral visualization mapping all 100 cantos with color-coded realms, sized by word count, with sentiment glow effects
- **Emotional Arc** - Sentiment analysis chart showing the emotional progression from the darkness of Inferno through the light of Paradiso
- **Character Network** - Force-directed graph of character co-occurrences and relationships across all three realms
- **Thematic Radial Chart** - Radial visualization showing the distribution of 16 key themes, filterable by realm
- **Canto Explorer** - Detailed explorer with search, per-canto statistics, sentiment breakdowns, character lists, word frequencies, and notable passages

## Prerequisites

- **Python 3.8+** (for text extraction and analysis)
- **Node.js 16+** (for the visualization app)

## Setup

### 1. Python Environment (Data Extraction)

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Text Extraction & Analysis

```bash
python extract_and_analyze.py
```

This processes the PDF and generates four JSON datasets in `src/data/`:
- `divine-comedy-data.json` - Main structured dataset (cantos, characters, themes, sentiment)
- `network-data.json` - Character co-occurrence network
- `journey-data.json` - Spatial journey coordinates for spiral visualization
- `symbols-data.json` - Rivers, creatures, celestial bodies, references

### 3. Visualization App

```bash
# Install Node.js dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

The app will be available at `http://localhost:5173`.

## Project Structure

```
divine-comedy-viz/
  extract_and_analyze.py     # Python: PDF extraction + NLP analysis
  divine-comedy.pdf          # Source text (Longfellow translation)
  analysis-report.md         # Summary of analysis findings
  requirements.txt           # Python dependencies
  package.json               # Node.js dependencies
  index.html                 # Entry point
  vite.config.js             # Vite configuration
  src/
    App.svelte               # Main application layout
    app.css                  # Global styles
    main.js                  # Svelte mount point
    components/
      SpiralJourney.svelte   # Spiral descent/ascent visualization
      SentimentFlow.svelte   # Emotional arc line/area chart
      NetworkGraph.svelte    # Force-directed character network
      ThemeRadial.svelte     # Radial theme distribution chart
      CantoExplorer.svelte   # Detailed canto browser
    data/
      divine-comedy-data.json
      network-data.json
      journey-data.json
      symbols-data.json
    utils/
      dataProcessing.js      # Data loading and color utilities
      d3Helpers.js            # D3.js helper functions
```

## Data Pipeline

1. **PDF Extraction** (`pdfplumber`): Parses the decorative-header PDF format, splitting text into 100 cantos across 3 realms
2. **Text Cleaning**: Removes page headers, page numbers, and formatting artifacts
3. **Sentiment Analysis** (`NLTK VADER`): Computes compound, positive, negative, and neutral scores per canto
4. **Frequency Analysis**: Word frequencies, character mentions, theme keyword counting
5. **Network Building**: Character co-occurrence matrix from shared canto appearances
6. **Spatial Mapping**: Journey coordinates for spiral visualization

## Design

- **Color Palette**: Inferno (deep reds, purples), Purgatorio (earth tones), Paradiso (blues, golds)
- **Typography**: EB Garamond and Crimson Text (elegant serif fonts)
- **Dark Theme**: Deep dark background reflecting the cosmic journey
- **Responsive**: Works on desktop and mobile

## Credits

- Text: *The Divine Comedy* by Dante Alighieri, translated by Henry Wadsworth Longfellow
- PDF Source: Penn State Electronic Classics Series
- Built with: Svelte 5, D3.js v7, NLTK, pdfplumber
