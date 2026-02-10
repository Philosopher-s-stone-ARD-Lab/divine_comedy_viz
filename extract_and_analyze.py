"""
Divine Comedy PDF Text Extraction & Analysis
=============================================
Extracts text from the Longfellow translation PDF, parses structure,
performs NLP analysis, and generates JSON datasets for visualization.
"""

import pdfplumber
import re
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import nltk
import numpy as np
import pandas as pd

# Download required NLTK data
nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('averaged_perceptron_tagger_eng', quiet=True)

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

# ─── Constants ───────────────────────────────────────────────────────

PDF_PATH = "divine-comedy.pdf"
OUTPUT_DIR = Path("src/data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STOP_WORDS = set(stopwords.words('english'))
# Add archaic/common words that aren't meaningful
STOP_WORDS.update([
    'thou', 'thee', 'thy', 'thine', 'hath', 'doth', 'dost',
    'art', 'wast', 'wert', 'hast', 'shalt', 'wouldst', 'didst',
    'upon', 'unto', 'whence', 'hence', 'thereof', 'therein',
    'thereof', 'wherein', 'wherefore', 'ere', 'tis', 'twas',
    'thus', 'yet', 'one', 'would', 'could', 'said', 'made',
    'still', 'even', 'much', 'may', 'us', 'also', 'might',
    'shall', 'let', 'like', 'come', 'came', 'went', 'now',
    'two', 'first', 'well', 'without', 'many', 'ever', 'never',
    'say', 'go', 'see', 'saw', 'make', 'know', 'knew', 'take',
    'took', 'give', 'gave', 'turn', 'turned', 'began', 'back',
    'toward', 'towards', 'already', 'another'
])

REALM_NAMES = ['Inferno', 'Purgatorio', 'Paradiso']

# Known characters from the Divine Comedy
# NOTE: This is a curated list. Manual enrichment recommended for completeness.
KNOWN_CHARACTERS = {
    # Main characters
    'Virgil': {'role': 'Guide', 'realms': ['Inferno', 'Purgatorio'], 'significance': "Dante's guide through Hell and Purgatory, representing Reason", 'aliases': ['Virgilius']},
    'Beatrice': {'role': 'Guide', 'realms': ['Purgatorio', 'Paradiso'], 'significance': "Dante's beloved, guide through Paradise, representing Divine Love"},
    'Dante': {'role': 'Protagonist', 'realms': ['Inferno', 'Purgatorio', 'Paradiso'], 'significance': 'The pilgrim, narrator of the journey'},

    # Inferno characters
    'Charon': {'role': 'Ferryman', 'realms': ['Inferno'], 'significance': 'Ferryman of the dead across Acheron'},
    'Minos': {'role': 'Judge', 'realms': ['Inferno'], 'significance': 'Judge of the damned, assigns circles'},
    'Cerberus': {'role': 'Guardian', 'realms': ['Inferno'], 'significance': 'Three-headed beast guarding the gluttons'},
    'Plutus': {'role': 'Guardian', 'realms': ['Inferno'], 'significance': 'Guardian of the Fourth Circle'},
    'Phlegyas': {'role': 'Ferryman', 'realms': ['Inferno'], 'significance': 'Ferryman across the Styx'},
    'Farinata': {'role': 'Soul', 'realms': ['Inferno'], 'significance': 'Ghibelline leader, heretic'},
    'Cavalcante': {'role': 'Soul', 'realms': ['Inferno'], 'significance': 'Father of Guido Cavalcanti'},
    'Pier della Vigna': {'role': 'Soul', 'realms': ['Inferno'], 'significance': 'Suicide, chancellor of Frederick II'},
    'Brunetto Latini': {'role': 'Soul', 'realms': ['Inferno'], 'significance': "Dante's former teacher"},
    'Ulysses': {'role': 'Soul', 'realms': ['Inferno'], 'significance': 'Greek hero punished for fraudulent counsel'},
    'Ugolino': {'role': 'Soul', 'realms': ['Inferno'], 'significance': 'Count imprisoned and starved with his children'},
    'Francesca': {'role': 'Soul', 'realms': ['Inferno'], 'significance': 'Lover punished in the circle of lust'},
    'Paolo': {'role': 'Soul', 'realms': ['Inferno'], 'significance': "Francesca's lover"},
    'Ciacco': {'role': 'Soul', 'realms': ['Inferno'], 'significance': 'Florentine glutton'},
    'Geryon': {'role': 'Monster', 'realms': ['Inferno'], 'significance': 'Monster of fraud, carries Dante and Virgil'},
    'Lucifer': {'role': 'Satan', 'realms': ['Inferno'], 'significance': 'Fallen angel trapped in ice at center of Hell'},
    'Satan': {'role': 'Satan', 'realms': ['Inferno'], 'significance': 'The Devil, imprisoned in the Ninth Circle'},
    'Minotaur': {'role': 'Guardian', 'realms': ['Inferno'], 'significance': 'Guardian of the Seventh Circle'},

    # Classical/Historical figures
    'Homer': {'role': 'Historical', 'realms': ['Inferno'], 'significance': 'Greek poet in Limbo'},
    'Horace': {'role': 'Historical', 'realms': ['Inferno'], 'significance': 'Roman poet in Limbo'},
    'Ovid': {'role': 'Historical', 'realms': ['Inferno'], 'significance': 'Roman poet in Limbo'},
    'Lucan': {'role': 'Historical', 'realms': ['Inferno'], 'significance': 'Roman poet in Limbo'},
    'Aristotle': {'role': 'Historical', 'realms': ['Inferno'], 'significance': 'Greek philosopher in Limbo'},
    'Plato': {'role': 'Historical', 'realms': ['Inferno'], 'significance': 'Greek philosopher in Limbo'},
    'Socrates': {'role': 'Historical', 'realms': ['Inferno'], 'significance': 'Greek philosopher in Limbo'},
    'Caesar': {'role': 'Historical', 'realms': ['Inferno'], 'significance': 'Roman ruler in Limbo'},
    'Cleopatra': {'role': 'Historical', 'realms': ['Inferno'], 'significance': 'In circle of lust'},
    'Helen': {'role': 'Historical', 'realms': ['Inferno'], 'significance': 'Helen of Troy, in circle of lust'},
    'Achilles': {'role': 'Historical', 'realms': ['Inferno'], 'significance': 'Greek hero in circle of lust'},

    # Purgatorio characters
    'Cato': {'role': 'Guardian', 'realms': ['Purgatorio'], 'significance': 'Guardian of Purgatory'},
    'Casella': {'role': 'Soul', 'realms': ['Purgatorio'], 'significance': 'Musician friend of Dante'},
    'Manfred': {'role': 'Soul', 'realms': ['Purgatorio'], 'significance': 'Excommunicated king'},
    'Sordello': {'role': 'Soul', 'realms': ['Purgatorio'], 'significance': 'Troubadour poet, guides through the Valley of Princes'},
    'Statius': {'role': 'Guide', 'realms': ['Purgatorio'], 'significance': 'Roman poet who accompanies Dante and Virgil'},
    'Matilda': {'role': 'Guide', 'realms': ['Purgatorio'], 'significance': 'Guardian of the Earthly Paradise'},

    # Paradiso characters
    'Justinian': {'role': 'Soul', 'realms': ['Paradiso'], 'significance': 'Byzantine Emperor in Mercury'},
    'Thomas Aquinas': {'role': 'Soul', 'realms': ['Paradiso'], 'significance': 'Dominican theologian in the Sun', 'aliases': ['Thomas']},
    'Bonaventure': {'role': 'Soul', 'realms': ['Paradiso'], 'significance': 'Franciscan theologian in the Sun'},
    'Cacciaguida': {'role': 'Soul', 'realms': ['Paradiso'], 'significance': "Dante's great-great-grandfather in Mars"},
    'Peter': {'role': 'Saint', 'realms': ['Paradiso'], 'significance': 'Apostle Peter in the Fixed Stars'},
    'Bernard': {'role': 'Guide', 'realms': ['Paradiso'], 'significance': 'Saint Bernard, final guide to the Beatific Vision'},
    'Mary': {'role': 'Saint', 'realms': ['Paradiso'], 'significance': 'The Virgin Mary, Queen of Heaven'},

    # Religious figures
    'Christ': {'role': 'Divine', 'realms': ['Paradiso'], 'significance': 'Jesus Christ'},
    'God': {'role': 'Divine', 'realms': ['Paradiso'], 'significance': 'The Divine Being'},
    'Adam': {'role': 'Soul', 'realms': ['Paradiso'], 'significance': 'First man, in Fixed Stars'},
    'Moses': {'role': 'Historical', 'realms': ['Inferno', 'Paradiso'], 'significance': 'Hebrew prophet'},
    'David': {'role': 'Historical', 'realms': ['Paradiso'], 'significance': 'King of Israel'},
    'Francis': {'role': 'Saint', 'realms': ['Paradiso'], 'significance': 'Saint Francis of Assisi'},
    'Dominic': {'role': 'Saint', 'realms': ['Paradiso'], 'significance': 'Saint Dominic'},
}

# Inferno divisions (Circles)
INFERNO_DIVISIONS = [
    {'circle': 0, 'name': 'Dark Wood / Vestibule', 'canto_range': [1, 3], 'sin_category': 'Ante-Inferno', 'punishment': 'Chasing a blank banner, stung by wasps', 'symbolism': ['Lost path', 'Moral confusion'], 'notable_characters': ['Virgil']},
    {'circle': 1, 'name': 'Limbo', 'canto_range': [4, 4], 'sin_category': None, 'punishment': 'Eternal longing without hope', 'symbolism': ['Unbaptized virtuous pagans'], 'notable_characters': ['Homer', 'Horace', 'Ovid', 'Lucan', 'Aristotle']},
    {'circle': 2, 'name': 'Lust', 'canto_range': [5, 5], 'sin_category': 'Incontinence', 'punishment': 'Blown about by violent storm', 'symbolism': ['Uncontrolled desire'], 'notable_characters': ['Francesca', 'Paolo', 'Cleopatra']},
    {'circle': 3, 'name': 'Gluttony', 'canto_range': [6, 6], 'sin_category': 'Incontinence', 'punishment': 'Lying in mud under rain of filth', 'symbolism': ['Excess consumption'], 'notable_characters': ['Ciacco', 'Cerberus']},
    {'circle': 4, 'name': 'Greed', 'canto_range': [7, 7], 'sin_category': 'Incontinence', 'punishment': 'Pushing heavy weights', 'symbolism': ['Material obsession'], 'notable_characters': ['Plutus']},
    {'circle': 5, 'name': 'Wrath', 'canto_range': [7, 9], 'sin_category': 'Incontinence', 'punishment': 'Fighting on surface / submerged in Styx', 'symbolism': ['Anger and sullenness'], 'notable_characters': ['Phlegyas']},
    {'circle': 6, 'name': 'Heresy', 'canto_range': [9, 11], 'sin_category': 'Heresy', 'punishment': 'Trapped in burning tombs', 'symbolism': ['Denial of afterlife'], 'notable_characters': ['Farinata', 'Cavalcante']},
    {'circle': 7, 'name': 'Violence', 'canto_range': [12, 17], 'sin_category': 'Violence', 'punishment': 'Various torments by ring', 'symbolism': ['Force against others, self, God/Nature'], 'notable_characters': ['Minotaur', 'Pier della Vigna', 'Brunetto Latini']},
    {'circle': 8, 'name': 'Fraud (Malebolge)', 'canto_range': [18, 30], 'sin_category': 'Fraud', 'punishment': 'Ten ditches of varied torment', 'symbolism': ['Deliberate deception'], 'notable_characters': ['Geryon', 'Ulysses']},
    {'circle': 9, 'name': 'Treachery', 'canto_range': [31, 34], 'sin_category': 'Treachery', 'punishment': 'Frozen in ice', 'symbolism': ['Betrayal of trust'], 'notable_characters': ['Ugolino', 'Lucifer']},
]

# Purgatorio divisions (Terraces)
PURGATORIO_DIVISIONS = [
    {'terrace': 0, 'name': 'Ante-Purgatory', 'canto_range': [1, 9], 'sin_category': 'Late repentance', 'penance': 'Waiting', 'virtue': 'Patience', 'notable_characters': ['Cato', 'Casella', 'Manfred', 'Sordello']},
    {'terrace': 1, 'name': 'Pride', 'canto_range': [10, 12], 'sin_category': 'Pride', 'penance': 'Carrying heavy stones', 'virtue': 'Humility', 'notable_characters': []},
    {'terrace': 2, 'name': 'Envy', 'canto_range': [13, 15], 'sin_category': 'Envy', 'penance': 'Eyes sewn shut with wire', 'virtue': 'Generosity', 'notable_characters': []},
    {'terrace': 3, 'name': 'Wrath', 'canto_range': [15, 17], 'sin_category': 'Wrath', 'penance': 'Walking in blinding smoke', 'virtue': 'Meekness', 'notable_characters': []},
    {'terrace': 4, 'name': 'Sloth', 'canto_range': [17, 19], 'sin_category': 'Sloth', 'penance': 'Ceaseless running', 'virtue': 'Zeal', 'notable_characters': []},
    {'terrace': 5, 'name': 'Avarice', 'canto_range': [19, 21], 'sin_category': 'Avarice', 'penance': 'Lying face down', 'virtue': 'Temperance', 'notable_characters': ['Statius']},
    {'terrace': 6, 'name': 'Gluttony', 'canto_range': [22, 24], 'sin_category': 'Gluttony', 'penance': 'Starving before fruit trees', 'virtue': 'Abstinence', 'notable_characters': []},
    {'terrace': 7, 'name': 'Lust', 'canto_range': [25, 27], 'sin_category': 'Lust', 'penance': 'Walking in flames', 'virtue': 'Chastity', 'notable_characters': []},
    {'terrace': 8, 'name': 'Earthly Paradise', 'canto_range': [28, 33], 'sin_category': None, 'penance': None, 'virtue': 'Perfection', 'notable_characters': ['Matilda', 'Beatrice']},
]

# Paradiso divisions (Spheres)
PARADISO_DIVISIONS = [
    {'sphere': 1, 'name': 'Moon', 'canto_range': [1, 5], 'virtue': 'Fortitude (broken vows)', 'celestial_body': 'Moon', 'notable_characters': []},
    {'sphere': 2, 'name': 'Mercury', 'canto_range': [5, 7], 'virtue': 'Justice (ambitious good)', 'celestial_body': 'Mercury', 'notable_characters': ['Justinian']},
    {'sphere': 3, 'name': 'Venus', 'canto_range': [8, 9], 'virtue': 'Temperance (lovers)', 'celestial_body': 'Venus', 'notable_characters': []},
    {'sphere': 4, 'name': 'Sun', 'canto_range': [10, 14], 'virtue': 'Prudence (wise)', 'celestial_body': 'Sun', 'notable_characters': ['Thomas Aquinas', 'Bonaventure']},
    {'sphere': 5, 'name': 'Mars', 'canto_range': [14, 18], 'virtue': 'Fortitude (warriors)', 'celestial_body': 'Mars', 'notable_characters': ['Cacciaguida']},
    {'sphere': 6, 'name': 'Jupiter', 'canto_range': [18, 20], 'virtue': 'Justice (just rulers)', 'celestial_body': 'Jupiter', 'notable_characters': []},
    {'sphere': 7, 'name': 'Saturn', 'canto_range': [21, 22], 'virtue': 'Temperance (contemplatives)', 'celestial_body': 'Saturn', 'notable_characters': ['Peter Damian']},
    {'sphere': 8, 'name': 'Fixed Stars', 'canto_range': [22, 27], 'virtue': 'Faith/Hope/Love', 'celestial_body': 'Fixed Stars', 'notable_characters': ['Peter', 'Adam']},
    {'sphere': 9, 'name': 'Primum Mobile', 'canto_range': [27, 29], 'virtue': 'Angels', 'celestial_body': 'Primum Mobile', 'notable_characters': []},
    {'sphere': 10, 'name': 'Empyrean', 'canto_range': [30, 33], 'virtue': 'Beatific Vision', 'celestial_body': 'Empyrean', 'notable_characters': ['Bernard', 'Mary']},
]

# Key themes to track
THEME_KEYWORDS = {
    'Love': ['love', 'beloved', 'desire', 'passion', 'affection', 'amore'],
    'Justice': ['justice', 'just', 'judge', 'judgment', 'punish', 'punishment', 'sentence', 'condemn'],
    'Sin': ['sin', 'sinful', 'sinners', 'guilt', 'wicked', 'evil', 'transgression'],
    'Virtue': ['virtue', 'virtuous', 'good', 'noble', 'worthy', 'righteous'],
    'Light': ['light', 'bright', 'radiance', 'luminous', 'splendour', 'splendor', 'shine', 'shining', 'gleam', 'glow'],
    'Darkness': ['dark', 'darkness', 'shadow', 'blind', 'obscure', 'night', 'black'],
    'Death': ['death', 'dead', 'die', 'dying', 'mortal', 'perish'],
    'Faith': ['faith', 'believe', 'belief', 'grace', 'pray', 'prayer', 'devotion'],
    'Suffering': ['pain', 'suffer', 'torment', 'weep', 'weeping', 'tears', 'grief', 'woe', 'lament', 'sorrow'],
    'Nature': ['earth', 'water', 'fire', 'wind', 'star', 'stars', 'sun', 'moon', 'sea', 'river', 'mountain'],
    'Knowledge': ['know', 'knowledge', 'wisdom', 'reason', 'truth', 'understand', 'intellect', 'mind', 'science'],
    'Power': ['power', 'king', 'lord', 'master', 'rule', 'reign', 'authority', 'empire'],
    'Beauty': ['beauty', 'beautiful', 'fair', 'lovely', 'sweet', 'gentle'],
    'Fear': ['fear', 'afraid', 'terror', 'dread', 'tremble', 'fright'],
    'Hope': ['hope', 'desire', 'wish', 'aspire', 'promise'],
    'Redemption': ['redeem', 'salvation', 'save', 'saved', 'mercy', 'forgive', 'forgiveness', 'pardon'],
}

# Symbolic elements to track
SYMBOLIC_RIVERS = ['Acheron', 'Styx', 'Phlegethon', 'Lethe', 'Eunoe', 'Cocytus']
SYMBOLIC_CREATURES = ['Leopard', 'Lion', 'Wolf', 'Eagle', 'Serpent', 'Griffin', 'Phoenix', 'Dragon']
CELESTIAL_BODIES = ['Sun', 'Moon', 'Mars', 'Mercury', 'Venus', 'Jupiter', 'Saturn', 'Stars']
SIGNIFICANT_NUMBERS = {'3': 'Trinity', '7': 'Seven deadly sins/virtues', '9': 'Nine circles/spheres', '10': 'Perfection', '33': 'Cantos per canticle', '100': 'Total cantos'}

# Religious references
RELIGIOUS_REFS = ['God', 'Christ', 'Jesus', 'Virgin', 'Mary', 'Satan', 'Devil', 'Lucifer',
                  'Heaven', 'Paradise', 'Hell', 'Angel', 'Angels', 'Holy', 'Sacred',
                  'Cross', 'Trinity', 'Church', 'Gospel', 'Scripture', 'Bible']
# Classical references
CLASSICAL_REFS = ['Homer', 'Virgil', 'Caesar', 'Aristotle', 'Plato', 'Socrates',
                  'Troy', 'Rome', 'Athens', 'Aeneas', 'Achilles', 'Ulysses',
                  'Jupiter', 'Mars', 'Apollo', 'Diana', 'Neptune', 'Juno', 'Minerva']


# ─── PDF Extraction ──────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path):
    """Extract all text from the PDF, skipping TOC pages."""
    print(f"Extracting text from {pdf_path}...")
    full_text = []
    # Running headers that appear as the first line on alternating pages
    RUNNING_HEADERS = {'Dante', 'Longfellow'}
    with pdfplumber.open(pdf_path) as pdf:
        # Skip first 6 pages (title, copyright, TOC)
        for i, page in enumerate(pdf.pages):
            if i < 6:
                continue
            text = page.extract_text()
            if text:
                # Strip running headers (author/translator names at top of pages)
                lines = text.split('\n')
                if lines and lines[0].strip() in RUNNING_HEADERS:
                    text = '\n'.join(lines[1:])
                full_text.append(text)
            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{len(pdf.pages)} pages")
    print(f"  Extracted text from {len(full_text)} pages (skipped 6 TOC pages)")
    return "\n".join(full_text)


def deduplicate_chars(s):
    """
    The PDF uses a decorative font that repeats each character ~5 times.
    E.g. 'IIIIInnnnnfffffeeeeerrrrrnnnnnooooo' => 'Inferno'
    Collapse runs of identical characters to a single character.
    """
    if not s:
        return s
    result = [s[0]]
    for ch in s[1:]:
        if ch != result[-1]:
            result.append(ch)
    return ''.join(result)


def parse_cantos(full_text):
    """Parse the full text into individual cantos grouped by realm."""
    # The PDF body uses decorative headers where each character is repeated ~5 times:
    # "IIIIInnnnnfffffeeeeerrrrrnnnnnooooo::::: CCCCCaaaaannnnntttttooooo IIIII"
    # We match these repeated-character headers.
    # Pattern: repeated chars forming realm name, colons, "Canto", roman numerals
    header_pattern = re.compile(
        r'(([IPp])\2{2,}([^\s:])\3{2,}([^\s:])\4{2,}([^\s:])\5{2,}([^\s:])\6{2,}([^\s:])\7{2,}(?:([^\s:])\8{2,}(?:([^\s:])\9{2,}(?:([^\s:])\10{2,})?)?)?\s*:+\s*[Cc]{2,}[Aa]{2,}[Nn]{2,}[Tt]{2,}[Oo]{2,}\s+([IVXLC]{2,}))',
        re.MULTILINE
    )

    # (removed problematic pattern)

    # Most reliable: find the decorative headers by looking for ":::::" pattern
    # which only appears in canto headers
    colon_pattern = re.compile(
        r'([A-Za-z]{15,}):{4,}\s+([A-Za-z]{15,})\s+([IVXLC ]{2,})',
        re.MULTILINE
    )

    headers_found = list(colon_pattern.finditer(full_text))
    print(f"  Found {len(headers_found)} decorative canto headers")

    if len(headers_found) < 50:
        # Fallback: try a broader pattern
        # Look for ":::::" as the marker
        broader = re.compile(r'(\S+):{3,}\s+(\S+)\s+([IVXLC]{1,}[IVXLC ]*)\b')
        headers_found = list(broader.finditer(full_text))
        print(f"  Fallback found {len(headers_found)} headers")

    cantos = []
    for idx, match in enumerate(headers_found):
        raw_realm = deduplicate_chars(match.group(1).strip())
        raw_canto_word = deduplicate_chars(match.group(2).strip())
        raw_roman = match.group(3).strip()
        # Collapse repeated roman numeral chars
        roman = deduplicate_chars(raw_roman.replace(' ', ''))

        # Normalize realm name
        realm = None
        rl = raw_realm.lower()
        if 'inferno' in rl:
            realm = 'Inferno'
        elif 'purgatorio' in rl or 'purga' in rl:
            realm = 'Purgatorio'
        elif 'paradiso' in rl or 'parad' in rl:
            realm = 'Paradiso'

        if not realm:
            continue

        canto_num = roman_to_int(roman)
        if canto_num == 0 or canto_num > 34:
            continue

        start_pos = match.end()
        end_pos = headers_found[idx + 1].start() if idx + 1 < len(headers_found) else len(full_text)

        canto_text = full_text[start_pos:end_pos].strip()
        # Clean up page headers ("Dante" or "Longfellow" appearing at page tops)
        canto_text = re.sub(r'\nDante\n', '\n', canto_text)
        canto_text = re.sub(r'\nLongfellow\n', '\n', canto_text)
        # Remove standalone page numbers
        canto_text = re.sub(r'\n\d{1,3}\n', '\n', canto_text)
        # Remove the "The Divine Comedy INFERNO/PURGATORIO/PARADISO" page header
        canto_text = re.sub(r'The Divine Comedy\s+(INFERNO|PURGATORIO|PARADISO)\s*', '', canto_text)

        cantos.append({
            'realm': realm,
            'number': canto_num,
            'global_number': len(cantos) + 1,
            'title': f"Canto {roman}",
            'text': canto_text,
            'header': f"{realm}: Canto {roman}"
        })

    print(f"  Parsed {len(cantos)} cantos")

    # Validate
    realms_count = Counter(c['realm'] for c in cantos)
    for r, count in realms_count.items():
        print(f"    {r}: {count} cantos")

    return cantos


def roman_to_int(s):
    """Convert Roman numeral to integer."""
    roman_vals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    result = 0
    for i in range(len(s)):
        if i + 1 < len(s) and roman_vals.get(s[i], 0) < roman_vals.get(s[i + 1], 0):
            result -= roman_vals.get(s[i], 0)
        else:
            result += roman_vals.get(s[i], 0)
    return result


# ─── Text Analysis ───────────────────────────────────────────────────

def analyze_sentiment(text):
    """Analyze sentiment of a text using VADER."""
    sia = SentimentIntensityAnalyzer()
    scores = sia.polarity_scores(text)
    return {
        'compound': round(scores['compound'], 4),
        'positive': round(scores['pos'], 4),
        'negative': round(scores['neg'], 4),
        'neutral': round(scores['neu'], 4)
    }


def get_word_frequencies(text, top_n=20):
    """Get word frequencies excluding stop words."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    counter = Counter(filtered)
    return counter.most_common(top_n)


def count_lines(text):
    """Count lines in a canto text."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    return len(lines)


def find_characters_in_text(text):
    """Find known character names in text, including aliases."""
    found = []
    for name, info in KNOWN_CHARACTERS.items():
        total = 0
        # Match the canonical name
        pattern = re.compile(r'\b' + re.escape(name) + r'\b', re.IGNORECASE)
        total += len(pattern.findall(text))
        # Match any aliases
        for alias in info.get('aliases', []):
            alias_pattern = re.compile(r'\b' + re.escape(alias) + r'\b', re.IGNORECASE)
            total += len(alias_pattern.findall(text))
        if total > 0:
            found.append({'name': name, 'count': total})
    return sorted(found, key=lambda x: x['count'], reverse=True)


def find_themes_in_text(text):
    """Count theme keyword occurrences in text."""
    text_lower = text.lower()
    theme_scores = {}
    for theme, keywords in THEME_KEYWORDS.items():
        count = 0
        for kw in keywords:
            count += len(re.findall(r'\b' + re.escape(kw) + r'\b', text_lower))
        if count > 0:
            theme_scores[theme] = count
    return theme_scores


def extract_quotes(text, max_quotes=3):
    """Extract notable quoted passages (dialogue markers)."""
    # Look for text in quotation marks or after speech indicators
    quote_patterns = [
        re.compile(r'["\u201c](.{20,120}?)["\u201d]'),  # Standard quotes
        re.compile(r'\u2018(.{20,120}?)\u2019'),  # Single quotes
    ]
    quotes = []
    for pattern in quote_patterns:
        for match in pattern.finditer(text):
            q = match.group(1).strip()
            if len(q) > 15:
                quotes.append(q)
    return quotes[:max_quotes]


def calculate_vocabulary_richness(text):
    """Calculate type-token ratio (vocabulary richness)."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    if not words:
        return 0
    return round(len(set(words)) / len(words), 4)


def count_religious_refs(text):
    """Count religious references."""
    counts = {}
    for ref in RELIGIOUS_REFS:
        c = len(re.findall(r'\b' + re.escape(ref) + r'\b', text, re.IGNORECASE))
        if c > 0:
            counts[ref] = c
    return counts


def count_classical_refs(text):
    """Count classical references."""
    counts = {}
    for ref in CLASSICAL_REFS:
        c = len(re.findall(r'\b' + re.escape(ref) + r'\b', text, re.IGNORECASE))
        if c > 0:
            counts[ref] = c
    return counts


def find_symbols_in_text(text):
    """Find symbolic elements in text."""
    found = {'rivers': [], 'creatures': [], 'celestial': []}
    text_lower = text.lower()
    for river in SYMBOLIC_RIVERS:
        if river.lower() in text_lower:
            found['rivers'].append(river)
    for creature in SYMBOLIC_CREATURES:
        if creature.lower() in text_lower:
            found['creatures'].append(creature)
    for body in CELESTIAL_BODIES:
        if body.lower() in text_lower:
            found['celestial'].append(body)
    return found


# ─── Main Analysis Pipeline ─────────────────────────────────────────

def analyze_cantos(cantos):
    """Run full analysis on all cantos."""
    print("\nRunning analysis on cantos...")
    sia = SentimentIntensityAnalyzer()

    for idx, canto in enumerate(cantos):
        text = canto['text']
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_count = len(words)

        # Sentiment
        sentiment = analyze_sentiment(text)
        canto['sentiment'] = sentiment

        # Word stats
        canto['word_count'] = word_count
        canto['line_count'] = count_lines(text)
        canto['vocabulary_richness'] = calculate_vocabulary_richness(text)
        canto['top_words'] = [{'word': w, 'count': c} for w, c in get_word_frequencies(text, 10)]

        # Characters
        canto['characters'] = find_characters_in_text(text)
        # Dante is the narrator of every canto — ensure he is always present
        # (his name rarely appears in the text since he uses first person)
        if not any(c['name'] == 'Dante' for c in canto['characters']):
            canto['characters'].insert(0, {'name': 'Dante', 'count': 1})

        # Themes
        canto['themes'] = find_themes_in_text(text)

        # Quotes
        canto['quotes'] = extract_quotes(text)

        # Symbols
        canto['symbols'] = find_symbols_in_text(text)

        # References
        canto['religious_refs'] = count_religious_refs(text)
        canto['classical_refs'] = count_classical_refs(text)

        if (idx + 1) % 20 == 0:
            print(f"  Analyzed {idx + 1}/{len(cantos)} cantos")

    print(f"  Analysis complete for {len(cantos)} cantos")
    return cantos


# ─── JSON Dataset Generation ────────────────────────────────────────

def generate_main_dataset(cantos):
    """Generate the main divine-comedy-data.json."""
    print("\nGenerating main dataset...")

    # Group cantos by realm
    realms_data = {}
    for canto in cantos:
        r = canto['realm']
        if r not in realms_data:
            realms_data[r] = []
        realms_data[r].append(canto)

    # Build realm objects
    realms = []
    realm_descriptions = {
        'Inferno': 'The descent through the nine circles of Hell',
        'Purgatorio': 'The ascent of the mountain of Purgatory',
        'Paradiso': 'The journey through the celestial spheres of Paradise'
    }

    realm_divisions_map = {
        'Inferno': INFERNO_DIVISIONS,
        'Purgatorio': PURGATORIO_DIVISIONS,
        'Paradiso': PARADISO_DIVISIONS,
    }

    for realm_name in REALM_NAMES:
        realm_cantos = realms_data.get(realm_name, [])

        # Aggregate top words for realm
        realm_text = ' '.join(c['text'] for c in realm_cantos)
        realm_top_words = [{'word': w, 'count': c} for w, c in get_word_frequencies(realm_text, 20)]

        # Aggregate themes
        realm_themes = defaultdict(int)
        for c in realm_cantos:
            for theme, count in c['themes'].items():
                realm_themes[theme] += count

        # Build canto entries (without raw text to keep JSON manageable)
        canto_entries = []
        for c in realm_cantos:
            location = determine_location(c['realm'], c['number'])
            canto_entries.append({
                'number': c['number'],
                'global_number': c['global_number'],
                'title': c['title'],
                'realm': c['realm'],
                'location': location,
                'line_count': c['line_count'],
                'word_count': c['word_count'],
                'vocabulary_richness': c['vocabulary_richness'],
                'characters': c['characters'],
                'key_themes': [{'theme': t, 'count': ct} for t, ct in sorted(c['themes'].items(), key=lambda x: -x[1])],
                'notable_quotes': c['quotes'],
                'sentiment': c['sentiment'],
                'top_words': c['top_words'],
                'symbols': c['symbols'],
                'religious_references': c['religious_refs'],
                'classical_references': c['classical_refs'],
            })

        # Prepare divisions
        divisions = realm_divisions_map.get(realm_name, [])
        division_entries = []
        for d in divisions:
            # Collect characters mentioned in these cantos
            div_cantos = [c for c in realm_cantos if d['canto_range'][0] <= c['number'] <= d['canto_range'][1]]
            souls = set()
            for dc in div_cantos:
                for ch in dc['characters']:
                    souls.add(ch['name'])

            entry = {**d, 'souls_mentioned': list(souls)}
            division_entries.append(entry)

        realms.append({
            'name': realm_name,
            'description': realm_descriptions.get(realm_name, ''),
            'canto_count': len(realm_cantos),
            'total_words': sum(c['word_count'] for c in realm_cantos),
            'total_lines': sum(c['line_count'] for c in realm_cantos),
            'avg_sentiment': round(np.mean([c['sentiment']['compound'] for c in realm_cantos]), 4) if realm_cantos else 0,
            'vocabulary_richness': calculate_vocabulary_richness(realm_text),
            'top_words': realm_top_words,
            'themes': [{'theme': t, 'count': ct} for t, ct in sorted(realm_themes.items(), key=lambda x: -x[1])],
            'cantos': canto_entries,
            'divisions': division_entries,
        })

    # Character list
    characters = []
    char_counts = defaultdict(lambda: {'total': 0, 'cantos': set(), 'realms': set()})
    for c in cantos:
        for ch in c['characters']:
            char_counts[ch['name']]['total'] += ch['count']
            char_counts[ch['name']]['cantos'].add(c['global_number'])
            char_counts[ch['name']]['realms'].add(c['realm'])

    for name, data in sorted(char_counts.items(), key=lambda x: -x[1]['total']):
        info = KNOWN_CHARACTERS.get(name, {'role': 'Unknown', 'significance': '', 'realms': []})
        characters.append({
            'name': name,
            'role': info.get('role', 'Unknown'),
            'total_mentions': data['total'],
            'appearances': sorted(data['cantos']),
            'realm_association': sorted(data['realms']),
            'significance': info.get('significance', ''),
        })

    # Theme aggregation
    all_themes = defaultdict(lambda: {'total': 0, 'by_realm': defaultdict(int)})
    for c in cantos:
        for theme, count in c['themes'].items():
            all_themes[theme]['total'] += count
            all_themes[theme]['by_realm'][c['realm']] += count

    themes = []
    for name, data in sorted(all_themes.items(), key=lambda x: -x[1]['total']):
        themes.append({
            'name': name,
            'total_frequency': data['total'],
            'by_realm': dict(data['by_realm']),
            'description': get_theme_description(name),
        })

    dataset = {
        'metadata': {
            'title': 'Divine Comedy',
            'author': 'Dante Alighieri',
            'translator': 'Henry Wadsworth Longfellow',
            'total_cantos': len(cantos),
            'structure': '3 realms, 100 cantos (34 + 33 + 33)',
        },
        'realms': realms,
        'characters': characters,
        'themes': themes,
    }

    return dataset


def determine_location(realm, canto_num):
    """Determine the location name for a given canto."""
    if realm == 'Inferno':
        for d in INFERNO_DIVISIONS:
            if d['canto_range'][0] <= canto_num <= d['canto_range'][1]:
                return d['name']
    elif realm == 'Purgatorio':
        for d in PURGATORIO_DIVISIONS:
            if d['canto_range'][0] <= canto_num <= d['canto_range'][1]:
                return d['name']
    elif realm == 'Paradiso':
        for d in PARADISO_DIVISIONS:
            if d['canto_range'][0] <= canto_num <= d['canto_range'][1]:
                return d['name']
    return 'Unknown'


def get_theme_description(theme_name):
    """Return a description for a theme."""
    descs = {
        'Love': 'Divine love, human love, and desire throughout the journey',
        'Justice': 'Divine justice and the moral order of the universe',
        'Sin': 'Transgression, guilt, and moral failure',
        'Virtue': 'Moral excellence and righteousness',
        'Light': 'Illumination, truth, and divine presence',
        'Darkness': 'Ignorance, evil, and absence of God',
        'Death': 'Mortality, the afterlife, and spiritual death',
        'Faith': 'Religious belief, prayer, and devotion',
        'Suffering': 'Pain, torment, and penance',
        'Nature': 'The natural world and its symbolic significance',
        'Knowledge': 'Wisdom, reason, and intellectual understanding',
        'Power': 'Authority, rulership, and divine power',
        'Beauty': 'Aesthetic and spiritual beauty',
        'Fear': 'Terror, dread, and awe',
        'Hope': 'Aspiration, desire, and expectation',
        'Redemption': 'Salvation, forgiveness, and divine mercy',
    }
    return descs.get(theme_name, '')


def generate_network_data(cantos):
    """Generate character co-occurrence network data."""
    print("\nGenerating network data...")

    # Build co-occurrence matrix
    cooccurrence = defaultdict(int)
    char_canto_map = defaultdict(set)

    for c in cantos:
        chars_in_canto = [ch['name'] for ch in c['characters']]
        for ch in chars_in_canto:
            char_canto_map[ch].add(c['global_number'])
        # Co-occurrences
        for i in range(len(chars_in_canto)):
            for j in range(i + 1, len(chars_in_canto)):
                pair = tuple(sorted([chars_in_canto[i], chars_in_canto[j]]))
                cooccurrence[pair] += 1

    # Build nodes
    nodes = []
    for name, canto_set in char_canto_map.items():
        info = KNOWN_CHARACTERS.get(name, {})
        realm_assoc = set()
        for c in cantos:
            if c['global_number'] in canto_set:
                realm_assoc.add(c['realm'])
        nodes.append({
            'id': name,
            'role': info.get('role', 'Unknown'),
            'mentions': len(canto_set),
            'realm_association': sorted(realm_assoc),
            'significance': info.get('significance', ''),
        })

    # Build links
    links = []
    for (src, tgt), weight in sorted(cooccurrence.items(), key=lambda x: -x[1]):
        if weight >= 1:
            links.append({
                'source': src,
                'target': tgt,
                'weight': weight,
            })

    network = {
        'nodes': nodes,
        'links': links,
    }
    return network


def generate_journey_data(cantos):
    """Generate spatial journey progression data."""
    print("\nGenerating journey data...")

    journey_points = []
    for c in cantos:
        g = c['global_number']
        realm = c['realm']

        # Calculate spatial coordinates for the spiral visualization
        # Inferno: descending spiral (negative y)
        # Purgatorio: ascending from 0 (positive y)
        # Paradiso: ascending further (higher positive y)
        if realm == 'Inferno':
            # Cantos 1-34: descend from 0 to -1
            progress = c['number'] / 34
            depth = -progress
            angle = progress * 3 * math.pi  # ~1.5 rotations
            x = math.cos(angle) * (1 - progress * 0.3)
            z = math.sin(angle) * (1 - progress * 0.3)
        elif realm == 'Purgatorio':
            # Cantos 1-33: ascend from 0 to 1
            progress = c['number'] / 33
            depth = progress
            angle = progress * 3 * math.pi
            x = math.cos(angle) * (0.7 + progress * 0.3)
            z = math.sin(angle) * (0.7 + progress * 0.3)
        else:  # Paradiso
            # Cantos 1-33: ascend from 1 to 2
            progress = c['number'] / 33
            depth = 1 + progress
            angle = progress * 3 * math.pi
            x = math.cos(angle) * (1 + progress * 0.5)
            z = math.sin(angle) * (1 + progress * 0.5)

        journey_points.append({
            'global_canto': g,
            'realm': realm,
            'canto_number': c['number'],
            'title': c['title'],
            'location': determine_location(realm, c['number']),
            'x': round(x, 4),
            'y': round(depth, 4),
            'z': round(z, 4),
            'angle': round(math.degrees(angle), 2),
            'sentiment': c['sentiment']['compound'],
            'word_count': c['word_count'],
            'dominant_theme': max(c['themes'].items(), key=lambda x: x[1])[0] if c['themes'] else 'None',
        })

    return {'journey': journey_points}


def generate_symbols_data(cantos):
    """Generate symbolic elements dataset."""
    print("\nGenerating symbols data...")

    rivers = defaultdict(list)
    creatures = defaultdict(list)
    celestial = defaultdict(list)

    for c in cantos:
        syms = c['symbols']
        for r in syms['rivers']:
            rivers[r].append({'canto': c['global_number'], 'realm': c['realm']})
        for cr in syms['creatures']:
            creatures[cr].append({'canto': c['global_number'], 'realm': c['realm']})
        for cb in syms['celestial']:
            celestial[cb].append({'canto': c['global_number'], 'realm': c['realm']})

    # Religious vs Classical reference distribution
    rel_by_realm = defaultdict(lambda: defaultdict(int))
    cls_by_realm = defaultdict(lambda: defaultdict(int))
    for c in cantos:
        for ref, count in c['religious_refs'].items():
            rel_by_realm[c['realm']][ref] += count
        for ref, count in c['classical_refs'].items():
            cls_by_realm[c['realm']][ref] += count

    symbols = {
        'rivers': {name: {'occurrences': occs, 'total': len(occs)} for name, occs in rivers.items()},
        'creatures': {name: {'occurrences': occs, 'total': len(occs)} for name, occs in creatures.items()},
        'celestial_bodies': {name: {'occurrences': occs, 'total': len(occs)} for name, occs in celestial.items()},
        'significant_numbers': SIGNIFICANT_NUMBERS,
        'religious_references': {realm: dict(refs) for realm, refs in rel_by_realm.items()},
        'classical_references': {realm: dict(refs) for realm, refs in cls_by_realm.items()},
    }
    return symbols


# ─── Main ────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Divine Comedy - Text Extraction & Analysis")
    print("=" * 60)

    # 1. Extract text
    full_text = extract_text_from_pdf(PDF_PATH)

    # 2. Parse into cantos
    cantos = parse_cantos(full_text)

    if not cantos:
        print("ERROR: No cantos were found. Check PDF format.")
        return

    # 3. Analyze
    cantos = analyze_cantos(cantos)

    # 4. Generate datasets
    main_data = generate_main_dataset(cantos)
    network_data = generate_network_data(cantos)
    journey_data = generate_journey_data(cantos)
    symbols_data = generate_symbols_data(cantos)

    # 5. Save JSON files
    def save_json(data, filename):
        path = OUTPUT_DIR / filename
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  Saved {path}")

    save_json(main_data, 'divine-comedy-data.json')
    save_json(network_data, 'network-data.json')
    save_json(journey_data, 'journey-data.json')
    save_json(symbols_data, 'symbols-data.json')

    # 6. Print summary
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    for realm in main_data['realms']:
        print(f"\n{realm['name']}:")
        print(f"  Cantos: {realm['canto_count']}")
        print(f"  Total words: {realm['total_words']}")
        print(f"  Avg sentiment: {realm['avg_sentiment']}")
        print(f"  Top themes: {', '.join(t['theme'] for t in realm['themes'][:5])}")

    print(f"\nTotal characters found: {len(main_data['characters'])}")
    print(f"Total themes tracked: {len(main_data['themes'])}")
    print(f"Network nodes: {len(network_data['nodes'])}, links: {len(network_data['links'])}")

    print("\nDone! JSON files saved to src/data/")


if __name__ == '__main__':
    main()
