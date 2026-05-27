from __future__ import annotations
"""
Scripture grounding service.

Responsibilities:
1. Extract verse references from user messages (regex)
2. Verify them against the live Bible API (hallucination prevention)
3. Detect user-provided incorrect quotations
4. Surface corrections to inject into LLM context
"""

import re
import httpx
import logging
from typing import Optional
from app.models import ScriptureRef
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Canonical book names + common abbreviations → normalised name for Bible API
BOOK_ALIASES: dict[str, str] = {
    "gen": "Genesis", "genesis": "Genesis",
    "exo": "Exodus", "ex": "Exodus", "exodus": "Exodus",
    "lev": "Leviticus", "leviticus": "Leviticus",
    "num": "Numbers", "numbers": "Numbers",
    "deu": "Deuteronomy", "deut": "Deuteronomy", "deuteronomy": "Deuteronomy",
    "jos": "Joshua", "josh": "Joshua", "joshua": "Joshua",
    "jdg": "Judges", "judg": "Judges", "judges": "Judges",
    "rut": "Ruth", "ruth": "Ruth",
    "1sa": "1 Samuel", "1sam": "1 Samuel", "1 samuel": "1 Samuel",
    "2sa": "2 Samuel", "2sam": "2 Samuel", "2 samuel": "2 Samuel",
    "1ki": "1 Kings", "1kgs": "1 Kings", "1 kings": "1 Kings",
    "2ki": "2 Kings", "2kgs": "2 Kings", "2 kings": "2 Kings",
    "1ch": "1 Chronicles", "1chr": "1 Chronicles", "1 chronicles": "1 Chronicles",
    "2ch": "2 Chronicles", "2chr": "2 Chronicles", "2 chronicles": "2 Chronicles",
    "ezr": "Ezra", "ezra": "Ezra",
    "neh": "Nehemiah", "nehemiah": "Nehemiah",
    "est": "Esther", "esther": "Esther",
    "job": "Job",
    "psa": "Psalms", "ps": "Psalms", "psalm": "Psalms", "psalms": "Psalms",
    "pro": "Proverbs", "prov": "Proverbs", "proverbs": "Proverbs",
    "ecc": "Ecclesiastes", "eccl": "Ecclesiastes", "ecclesiastes": "Ecclesiastes",
    "son": "Song of Solomon", "sos": "Song of Solomon", "song": "Song of Solomon", "songs": "Song of Solomon",
    "isa": "Isaiah", "is": "Isaiah", "isaiah": "Isaiah",
    "jer": "Jeremiah", "jeremiah": "Jeremiah",
    "lam": "Lamentations", "lamentations": "Lamentations",
    "eze": "Ezekiel", "ezek": "Ezekiel", "ezekiel": "Ezekiel",
    "dan": "Daniel", "daniel": "Daniel",
    "hos": "Hosea", "hosea": "Hosea",
    "joe": "Joel", "joel": "Joel",
    "amo": "Amos", "amos": "Amos",
    "oba": "Obadiah", "obadiah": "Obadiah",
    "jon": "Jonah", "jonah": "Jonah",
    "mic": "Micah", "micah": "Micah",
    "nah": "Nahum", "nahum": "Nahum",
    "hab": "Habakkuk", "habakkuk": "Habakkuk",
    "zep": "Zephaniah", "zeph": "Zephaniah", "zephaniah": "Zephaniah",
    "hag": "Haggai", "haggai": "Haggai",
    "zec": "Zechariah", "zech": "Zechariah", "zechariah": "Zechariah",
    "mal": "Malachi", "malachi": "Malachi",
    "mat": "Matthew", "matt": "Matthew", "mt": "Matthew", "matthew": "Matthew",
    "mar": "Mark", "mk": "Mark", "mark": "Mark",
    "luk": "Luke", "lk": "Luke", "luke": "Luke",
    "joh": "John", "jn": "John", "john": "John",
    "act": "Acts", "acts": "Acts",
    "rom": "Romans", "ro": "Romans", "romans": "Romans",
    "1co": "1 Corinthians", "1cor": "1 Corinthians", "1 corinthians": "1 Corinthians",
    "2co": "2 Corinthians", "2cor": "2 Corinthians", "2 corinthians": "2 Corinthians",
    "gal": "Galatians", "galatians": "Galatians",
    "eph": "Ephesians", "ephesians": "Ephesians",
    "phi": "Philippians", "phil": "Philippians", "php": "Philippians", "philippians": "Philippians",
    "col": "Colossians", "colossians": "Colossians",
    "1th": "1 Thessalonians", "1thes": "1 Thessalonians", "1 thessalonians": "1 Thessalonians",
    "2th": "2 Thessalonians", "2thes": "2 Thessalonians", "2 thessalonians": "2 Thessalonians",
    "1ti": "1 Timothy", "1tim": "1 Timothy", "1 timothy": "1 Timothy",
    "2ti": "2 Timothy", "2tim": "2 Timothy", "2 timothy": "2 Timothy",
    "tit": "Titus", "titus": "Titus",
    "phm": "Philemon", "philemon": "Philemon",
    "heb": "Hebrews", "hebrews": "Hebrews",
    "jas": "James", "jam": "James", "james": "James",
    "1pe": "1 Peter", "1pet": "1 Peter", "1 peter": "1 Peter",
    "2pe": "2 Peter", "2pet": "2 Peter", "2 peter": "2 Peter",
    "1jo": "1 John", "1jn": "1 John", "1 john": "1 John",
    "2jo": "2 John", "2jn": "2 John", "2 john": "2 John",
    "3jo": "3 John", "3jn": "3 John", "3 john": "3 John",
    "jud": "Jude", "jude": "Jude",
    "rev": "Revelation", "re": "Revelation", "revelation": "Revelation",
}

# Sorted longest-first so multi-word books match before abbreviations
_BOOK_PATTERN = "|".join(
    re.escape(k) for k in sorted(BOOK_ALIASES.keys(), key=len, reverse=True)
)
VERSE_RE = re.compile(
    rf"\b({_BOOK_PATTERN})\s+(\d+):(\d+)(?:-(\d+))?\b",
    re.IGNORECASE,
)


def extract_references(text: str) -> list[str]:
    """Return normalised verse references found in text, e.g. ['John 3:16']."""
    refs = []
    for m in VERSE_RE.finditer(text):
        book_key = m.group(1).lower()
        book = BOOK_ALIASES.get(book_key, m.group(1).title())
        chapter, verse = m.group(2), m.group(3)
        end_verse = m.group(4)
        ref = f"{book} {chapter}:{verse}" + (f"-{end_verse}" if end_verse else "")
        if ref not in refs:
            refs.append(ref)
    return refs


async def fetch_verse(reference: str) -> Optional[ScriptureRef]:
    """Fetch a verse from bible-api.com. Returns None if not found."""
    url = f"{settings.bible_api_base}/{reference.replace(' ', '%20')}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if "error" in data:
            return None
        text = data.get("text", "").strip()
        if not text:
            return None
        return ScriptureRef(
            reference=data.get("reference", reference),
            text=text,
            translation=data.get("translation_name", "King James Version"),
            relevance="direct",
        )
    except Exception as e:
        logger.warning(f"Bible API error for '{reference}': {e}")
        return None


async def ground_message(message: str) -> tuple[list[ScriptureRef], list[str]]:
    """
    Extract and verify all verse references in a message.
    Returns (verified_verses, corrections).
    """
    refs = extract_references(message)
    verified: list[ScriptureRef] = []
    corrections: list[str] = []

    for ref in refs:
        result = await fetch_verse(ref)
        if result:
            verified.append(result)
        else:
            corrections.append(
                f"Note: The reference '{ref}' could not be verified in the Bible. "
                "It may not exist or may be mis-cited."
            )

    return verified, corrections
