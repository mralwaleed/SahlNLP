"""
Pre-compiled regex patterns and Unicode constants for Arabic text processing.

All patterns are compiled at module load time for maximum performance.
"""

import re

# ---------------------------------------------------------------------------
# Arabic Unicode Ranges
# ---------------------------------------------------------------------------
# Arabic letters (base):          U+0621 – U+063A
# Arabic letters (extended):      U+0641 – U+064A
# Arabic diacritics (tashkeel):   U+064B – U+065F
# Arabic-Indic digits:            U+0660 – U+0669
# Extended Arabic letters:        U+0671 – U+06D3
# Tatweel (Kashida):              U+0640

# ---------------------------------------------------------------------------
# Diacritics (Tashkeel)
# ---------------------------------------------------------------------------
ARABIC_DIACRITICS = frozenset({
    '\u064B',  # Fathatan
    '\u064C',  # Dammatan
    '\u064D',  # Kasratan
    '\u064E',  # Fatha
    '\u064F',  # Damma
    '\u0650',  # Kasra
    '\u0651',  # Shadda
    '\u0652',  # Sukun
    '\u0653',  # Maddah above
    '\u0654',  # Hamza above
    '\u0655',  # Hamza below
    '\u0656',  # Subscript alef
    '\u0657',  # Inverted damma
    '\u0658',  # Mark noon ghunna
    '\u0659',  # Zwarakay
    '\u065A',  # Vowel sign
    '\u065B',  # Inverted small v
    '\u065C',  # Small fatha
    '\u065D',  # Small waw
    '\u065E',  # Small yaa
    '\u065F',  # Small high seen
})

# Regex: any Arabic diacritical mark
RE_TASHKEEL = re.compile(r'[\u064B-\u065F]')

# ---------------------------------------------------------------------------
# Tatweel (Kashida)
# ---------------------------------------------------------------------------
TATWEEL = '\u0640'
RE_TATWEEL = re.compile(r'\u0640+')

# ---------------------------------------------------------------------------
# HTML & URLs
# ---------------------------------------------------------------------------
RE_HTML_TAGS = re.compile(r'<[^>]+>')
RE_URL = re.compile(
    r'https?://[^\s<>"{}|\\^`\[\]]+'
    r'|www\.[^\s<>"{}|\\^`\[\]]+',
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Repeated Characters
# ---------------------------------------------------------------------------
RE_REPEATED_CHAR = re.compile(r'(.)\1{2,}')

# ---------------------------------------------------------------------------
# Hamza normalization mappings
# ---------------------------------------------------------------------------
ALEF_VARIANTS = frozenset({'\u0622', '\u0623', '\u0625'})  # آ أ إ
ALEF = '\u0627'  # ا

# ---------------------------------------------------------------------------
# Taa / Yaa normalization
# ---------------------------------------------------------------------------
TAA_MARBUTA = '\u0629'  # ة
HAA = '\u0647'           # ه
ALEF_MAKSURA = '\u0649'  # ى
YAA = '\u064A'           # ي

# ---------------------------------------------------------------------------
# Arabic-Indic Digit Mappings
# ---------------------------------------------------------------------------
INDIC_TO_ARABIC_MAP = {
    '\u0660': '0',  # ٠
    '\u0661': '1',  # ١
    '\u0662': '2',  # ٢
    '\u0663': '3',  # ٣
    '\u0664': '4',  # ٤
    '\u0665': '5',  # ٥
    '\u0666': '6',  # ٦
    '\u0667': '7',  # ٧
    '\u0668': '8',  # ٨
    '\u0669': '9',  # ٩
}

ARABIC_TO_INDIC_MAP = {v: k for k, v in INDIC_TO_ARABIC_MAP.items()}

RE_INDIC_DIGITS = re.compile(r'[٠-٩]')
RE_ARABIC_DIGITS = re.compile(r'[0-9]')

# ---------------------------------------------------------------------------
# Tafkeet (Number to Arabic Words) — Full Grammar Support
# ---------------------------------------------------------------------------

# Base digit/teen words (0-19)
ARABIC_ONES = {
    0: 'صفر',
    1: 'واحد',
    2: 'اثنان',
    3: 'ثلاثة',
    4: 'أربعة',
    5: 'خمسة',
    6: 'ستة',
    7: 'سبعة',
    8: 'ثمانية',
    9: 'تسعة',
    10: 'عشرة',
    11: 'أحد عشر',
    12: 'اثنا عشر',
    13: 'ثلاثة عشر',
    14: 'أربعة عشر',
    15: 'خمسة عشر',
    16: 'ستة عشر',
    17: 'سبعة عشر',
    18: 'ثمانية عشر',
    19: 'تسعة عشر',
}

# Tens (20-90) with case variants
# Nominative: عشرون, ثلاثون...  Accusative/Genitive: عشرين, ثلاثين...
ARABIC_TENS_NOMINATIVE = {
    2: 'عشرون',
    3: 'ثلاثون',
    4: 'أربعون',
    5: 'خمسون',
    6: 'ستون',
    7: 'سبعون',
    8: 'ثمانون',
    9: 'تسعون',
}

ARABIC_TENS_ACCUSATIVE = {
    2: 'عشرين',
    3: 'ثلاثين',
    4: 'أربعين',
    5: 'خمسين',
    6: 'ستين',
    7: 'سبعين',
    8: 'ثمانين',
    9: 'تسعين',
}

# Backward-compatible default (nominative)
ARABIC_TENS = ARABIC_TENS_NOMINATIVE

# Hundreds with case variants
# Nominative: مائتان  Accusative/Genitive: مائتين
ARABIC_HUNDREDS_NOMINATIVE = {
    1: 'مائة',
    2: 'مائتان',
    3: 'ثلاثمائة',
    4: 'أربعمائة',
    5: 'خمسمائة',
    6: 'ستمائة',
    7: 'سبعمائة',
    8: 'ثمانمائة',
    9: 'تسعمائة',
}

ARABIC_HUNDREDS_ACCUSATIVE = {
    1: 'مائة',
    2: 'مائتين',
    3: 'ثلاثمائة',
    4: 'أربعمائة',
    5: 'خمسمائة',
    6: 'ستمائة',
    7: 'سبعمائة',
    8: 'ثمانمائة',
    9: 'تسعمائة',
}

# Backward-compatible default (nominative)
ARABIC_HUNDREDS = ARABIC_HUNDREDS_NOMINATIVE

# Scale (thousands, millions, billions, trillions) with case variants
# Each: (singular, dual_nominative, dual_accusative, plural_genitive)
ARABIC_SCALE_NOMINATIVE = {
    1: ('ألف', 'ألفان', 'آلاف'),
    2: ('مليون', 'مليونان', 'ملايين'),
    3: ('مليار', 'ملياران', 'مليارات'),
    4: ('تريليون', 'تريليونان', 'تريليونات'),
}

ARABIC_SCALE_ACCUSATIVE = {
    1: ('ألفاً', 'ألفين', 'آلاف'),
    2: ('مليوناً', 'مليونين', 'ملايين'),
    3: ('ملياراً', 'مليارين', 'مليارات'),
    4: ('تريليوناً', 'تريليونين', 'تريليونات'),
}

# Backward-compatible default (nominative)
ARABIC_SCALE = ARABIC_SCALE_NOMINATIVE

# ---------------------------------------------------------------------------
# PII Detection Patterns (Guardian Module)
# ---------------------------------------------------------------------------

# Saudi mobile numbers: +9665xxxxxxxx, 05xxxxxxxx, 5xxxxxxxx (8 trailing digits)
# Saudi mobile numbers: +9665xxxxxxxx, 05xxxxxxxx, 5xxxxxxxx
# Matches 9 digits (bare 5...) or 10 digits (05...) with optional spaces/dashes
RE_SA_PHONE = re.compile(
    r'(?<!\d)'
    r'(?:\+966[\s-]*)?'
    r'0?5'
    r'\d'
    r'(?:[\s-]*\d){7}'
    r'(?!\d)'
)

# Saudi National ID / IQAMA: exactly 10 digits starting with 1 or 2
RE_SA_ID = re.compile(
    r'(?<!\d)'
    r'[12]\d{9}'
    r'(?!\d)'
)

# Saudi IBAN: SA followed by 22 digits (total 24 chars), with optional spaces
RE_SA_IBAN = re.compile(
    r'\bSA\s*\d{2}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{2}\b'
    r'|\bSA\d{22}\b',
    re.IGNORECASE,
)

# Email addresses (RFC 5322 simplified)
RE_EMAIL = re.compile(
    r'[a-zA-Z0-9._%+\-]+'
    r'@'
    r'[a-zA-Z0-9.\-]+'
    r'\.'
    r'[a-zA-Z]{2,}'
)

# Arabic name contextual prefixes — titles and honorifics that signal a name follows
AR_NAME_PREFIXES = (
    "السيد",
    "السيدة",
    "الأستاذ",
    "الاستاذ",
    "الأستاذة",
    "الاستاذة",
    "الدكتور",
    "الدكتورة",
    "الطبيب",
    "الطبيبة",
    "المهندس",
    "المهندسة",
    "الأخ",
    "الاخ",
    "الأخت",
    "الاخت",
    "الشيخ",
    "الشيخة",
    "المعالي",
    "الفضيلة",
    "السعادة",
    "سعادة",
    "معالي",
    "فضيلة",
    "سعادة",
)

# Arabic name components — common theophoric and patronymic prefixes
AR_NAME_PARTICLES = (
    "عبد",
    "بن",
    "بنت",
    "آل",
    "ال",
)

# Regex: name preceded by a title, capturing 1-4 Arabic words after the title
# Matches: "السيد أحمد محمد علي" -> captures "أحمد محمد علي"
RE_AR_NAME_TITLED = re.compile(
    r'(?:' + '|'.join(AR_NAME_PREFIXES) + r')'
    r'\s+'
    r'([\u0621-\u063A\u0641-\u064A\u0671-\u06D3]+'
    r'(?:\s+[\u0621-\u063A\u0641-\u064A\u0671-\u06D3]+){0,3})'
)

# Regex: theophoric/patronymic names (عبد X, بن X) — 2-4 word sequences
RE_AR_NAME_THEOPHORIC = re.compile(
    r'\b'
    r'(?:عبد[\u0621-\u063A\u0641-\u064A]+|بن[\u0621-\u063A\u0641-\u064A]+)'
    r'(?:\s+[\u0621-\u063A\u0641-\u064A]+){0,2}'
    r'\b'
)
