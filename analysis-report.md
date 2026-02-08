# Divine Comedy - Text Analysis Report

## Overview

This report summarizes the results of automated text extraction and NLP analysis performed on the Longfellow translation of Dante's *Divine Comedy*. The source PDF (Penn State Electronic Classics edition) was parsed using `pdfplumber`, and analysis was conducted using NLTK's VADER sentiment analyzer alongside custom regex-based pattern extraction.

**Source**: `divine-comedy.pdf` (Longfellow translation, Penn State Electronic Classics)
**Extraction Method**: pdfplumber with decorative-header pattern matching
**Total Cantos Parsed**: 100 (34 Inferno + 33 Purgatorio + 33 Paradiso)

---

## Structural Analysis

| Metric | Inferno | Purgatorio | Paradiso | Total |
|--------|---------|------------|----------|-------|
| Cantos | 34 | 33 | 33 | 100 |
| Words | 29,945 | 29,647 | 30,504 | 90,096 |
| Lines | 2,779 | 2,782 | 2,942 | 8,503 |
| Avg Words/Canto | ~881 | ~898 | ~924 | ~901 |
| Vocabulary Richness | 17.16% | 17.07% | 17.02% | - |

**Key Finding**: The three realms are remarkably balanced in word count (~30,000 each), reflecting Dante's commitment to structural symmetry. Paradiso has slightly more words per canto on average.

---

## Sentiment Analysis

| Realm | Avg Compound Sentiment |
|-------|----------------------|
| Inferno | **-0.4067** (Negative) |
| Purgatorio | **+0.8793** (Positive) |
| Paradiso | **+0.9991** (Very Positive) |

The sentiment analysis confirms the expected emotional arc of the poem: a descent into negativity in Inferno, transitioning to strongly positive emotional content in Purgatorio and Paradiso. The near-perfect +0.999 score for Paradiso reflects the overwhelmingly positive language of divine love, light, and spiritual ecstasy.

**Note**: VADER sentiment analysis is calibrated for modern English. Archaic vocabulary and the translation's formal register may introduce some measurement noise.

---

## Thematic Analysis

### Top Themes by Frequency (All Realms)

1. **Nature** (569) - Natural imagery (earth, water, fire, stars, sun, moon) pervades all three realms
2. **Knowledge** (372) - Intellectual understanding, wisdom, and reason
3. **Love** (295) - Increases dramatically from Inferno (41) to Paradiso (163)
4. **Virtue** (285) - Moral excellence, most prominent in Purgatorio and Paradiso
5. **Power** (283) - Authority and rulership, strongest in Inferno (123)
6. **Light** (231) - Almost absent in Inferno (23), dominant in Paradiso (157)
7. **Suffering** (179) - Concentrated in Inferno (92), diminishes through the journey
8. **Beauty** (177) - Fairly evenly distributed across realms
9. **Faith** (175) - Grows from Inferno (22) to Paradiso (99)
10. **Hope** (169) - Present throughout, slightly increasing

### Thematic Progression

The data reveals clear thematic arcs:
- **Love** quadruples from Inferno to Paradiso (41 to 163)
- **Light** increases nearly 7x from Inferno to Paradiso (23 to 157)
- **Suffering** drops 5x from Inferno to Paradiso (92 to 19)
- **Fear** drops 6x from Inferno to Paradiso (49 to 8)
- **Power** decreases as the journey ascends (123 to 72)

---

## Character Analysis

### Most Mentioned Characters

| Character | Total Mentions | Cantos Appeared | Realms |
|-----------|---------------|-----------------|--------|
| God | 133 | 62 | All three |
| Beatrice | 65 | 36 | All three |
| Dante | 48 | 43 | All three |
| Christ | 42 | 21 | Purgatorio, Paradiso |
| Peter | 22 | 17 | All three |
| Mary | 20 | 16 | Purgatorio, Paradiso |
| Caesar | 12 | 9 | All three |
| Sordello | 8 | 4 | Purgatorio |
| Statius | 8 | 7 | Purgatorio |
| Minos | 8 | 7 | Inferno, Paradiso, Purgatorio |

### Character Network

The character co-occurrence network reveals 45 unique characters with 191 connections. The strongest relationships are:

- **Beatrice-God** (30 co-occurrences) - They appear together most frequently
- **Dante-God** (26) - The protagonist's journey is fundamentally about encountering the divine
- **Beatrice-Dante** (19) - The central human relationship
- **Christ-God** (16) - Theological content
- **Beatrice-Christ** (14) - Beatrice as intermediary

---

## Symbolic Elements

### Rivers
All six major rivers of the afterlife were detected:
- **Acheron** - River at the entrance to Hell
- **Styx** - River of wrath in the Fifth Circle
- **Phlegethon** - River of boiling blood (Seventh Circle)
- **Cocytus** - Frozen lake at the center of Hell
- **Lethe** - River of forgetfulness in the Earthly Paradise
- **Eunoe** - River of good memory in the Earthly Paradise

### Creatures
Seven symbolic creatures identified: Lion, Wolf, Eagle, Serpent, Phoenix, Dragon, Griffin

### Celestial Bodies
All eight celestial spheres detected: Sun, Stars, Moon, Mars, Saturn, Venus, Mercury, Jupiter

---

## Vocabulary Analysis

### Top Words by Realm

**Inferno**: master (81), great (64), within (61), people (61), eyes (60)
- "Master" reflects Dante's constant address to Virgil as guide
- "People" reflects the focus on condemned souls

**Purgatorio**: eyes (97), good (76), little (58), love (55), sun (54)
- "Eyes" dominate as visual perception becomes central
- "Love" and "sun" signal the transition toward the divine

**Paradiso**: light (107), love (94), eyes (91), heaven (72), great (70)
- "Light" is the defining word of Paradise
- "Love" reaches its peak frequency here

### Vocabulary Richness

All three realms have similar vocabulary richness (~17%), indicating consistent linguistic complexity across the translation. This uniformity likely reflects Longfellow's consistent translation style rather than variation in Dante's original Italian.

---

## Limitations and Recommendations

### Data Accuracy Notes
- PDF extraction from decorative fonts required special handling (character deduplication)
- Some page headers ("Dante", "Longfellow") were embedded in text and cleaned
- Character detection relies on a curated list; minor characters may be missed
- Sentiment analysis uses VADER, which is optimized for modern English

### Recommended Manual Enrichment
- Sin classifications for Inferno circles (partially provided via curated data)
- Detailed symbolism interpretation for each canto
- Cross-referencing with Italian original for translation accuracy
- Adding characters not in the curated list
- Temporal markers and time-of-day references throughout the narrative

---

*Report generated automatically by `extract_and_analyze.py`*
