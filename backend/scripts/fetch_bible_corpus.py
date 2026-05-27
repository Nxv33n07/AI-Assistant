from __future__ import annotations
"""
One-time setup script: fetches ~250 key Scripture passages from bible-api.com
and writes them to backend/data/key_verses.json for the RAG index.

Run from the backend/ directory:
    python scripts/fetch_bible_corpus.py
"""

import json, time, sys
from pathlib import Path
import urllib.request, urllib.parse

BASE = "https://bible-api.com"
OUT  = Path(__file__).parent.parent / "data" / "key_verses.json"

# (reference, topics)
KEY_VERSES = [
    # ── Creation / God's Nature ────────────────────────────────────────────
    ("Genesis 1:1",          ["creation", "god"]),
    ("Genesis 1:27",         ["creation", "humanity", "image of god"]),
    ("Genesis 2:24",         ["marriage", "family"]),
    ("Deuteronomy 6:4-5",    ["monotheism", "love", "commandment"]),
    ("Isaiah 6:3",           ["holiness", "god", "worship"]),
    ("Isaiah 55:8-9",        ["god", "wisdom", "sovereignty"]),
    ("Jeremiah 17:9",        ["human nature", "sin"]),
    ("Malachi 3:6",          ["god", "immutability"]),
    # ── Psalms ────────────────────────────────────────────────────────────
    ("Psalms 1:1-2",         ["blessing", "scripture", "meditation"]),
    ("Psalms 19:1",          ["creation", "glory of god", "worship"]),
    ("Psalms 23:1-6",        ["shepherd", "comfort", "trust"]),
    ("Psalms 27:1",          ["faith", "fear", "trust"]),
    ("Psalms 34:8",          ["worship", "trust", "taste and see"]),
    ("Psalms 37:4",          ["desire", "delight", "trust"]),
    ("Psalms 46:1",          ["comfort", "strength", "refuge"]),
    ("Psalms 46:10",         ["stillness", "prayer", "god"]),
    ("Psalms 51:10",         ["repentance", "forgiveness", "heart"]),
    ("Psalms 91:1-2",        ["protection", "refuge", "trust"]),
    ("Psalms 107:1",         ["thanksgiving", "worship"]),
    ("Psalms 118:24",        ["joy", "worship", "thanksgiving"]),
    ("Psalms 119:105",       ["scripture", "guidance", "light"]),
    ("Psalms 121:1-2",       ["help", "trust", "creator"]),
    ("Psalms 139:14",        ["creation", "humanity", "wonder"]),
    ("Psalms 147:3",         ["healing", "comfort", "brokenhearted"]),
    # ── Proverbs / Wisdom ─────────────────────────────────────────────────
    ("Proverbs 3:5-6",       ["trust", "guidance", "wisdom"]),
    ("Proverbs 4:23",        ["heart", "wisdom", "conduct"]),
    ("Proverbs 16:9",        ["plans", "sovereignty", "wisdom"]),
    ("Proverbs 17:17",       ["friendship", "love"]),
    ("Proverbs 22:6",        ["children", "family", "upbringing"]),
    # ── Major Prophets ────────────────────────────────────────────────────
    ("Isaiah 9:6",           ["messiah", "christmas", "prophecy"]),
    ("Isaiah 40:31",         ["strength", "hope", "waiting on god"]),
    ("Isaiah 41:10",         ["fear not", "strength", "help"]),
    ("Isaiah 43:2",          ["suffering", "protection", "presence of god"]),
    ("Isaiah 53:5-6",        ["atonement", "suffering servant", "salvation"]),
    ("Jeremiah 29:11",       ["hope", "future", "plans of god"]),
    ("Lamentations 3:22-23", ["mercy", "faithfulness", "new every morning"]),
    # ── Minor Prophets ────────────────────────────────────────────────────
    ("Micah 6:8",            ["justice", "mercy", "humility"]),
    ("Habakkuk 3:17-18",     ["faith", "joy", "suffering"]),
    # ── Gospels: Matthew ──────────────────────────────────────────────────
    ("Matthew 5:3-12",       ["beatitudes", "blessed", "sermon on the mount"]),
    ("Matthew 5:14-16",      ["light", "witness", "salt and light"]),
    ("Matthew 5:44",         ["love", "enemies", "prayer"]),
    ("Matthew 6:9-13",       ["prayer", "lord's prayer"]),
    ("Matthew 6:33",         ["kingdom of god", "seek first", "priorities"]),
    ("Matthew 7:7-8",        ["prayer", "ask seek knock"]),
    ("Matthew 11:28-30",     ["rest", "burden", "yoke of christ"]),
    ("Matthew 16:18",        ["church", "peter", "foundation"]),
    ("Matthew 22:37-39",     ["commandment", "love", "greatest"]),
    ("Matthew 25:40",        ["service", "least of these", "kingdom"]),
    ("Matthew 28:19-20",     ["great commission", "baptism", "discipleship"]),
    # ── Gospels: Mark ─────────────────────────────────────────────────────
    ("Mark 9:23",            ["faith", "belief", "miracles"]),
    ("Mark 10:27",           ["impossible", "faith", "god"]),
    ("Mark 16:15",           ["great commission", "gospel", "evangelism"]),
    # ── Gospels: Luke ─────────────────────────────────────────────────────
    ("Luke 1:37",            ["faith", "impossible", "gabriel"]),
    ("Luke 6:31",            ["golden rule", "ethics", "love"]),
    ("Luke 19:10",           ["salvation", "lost", "son of man"]),
    # ── Gospels: John ─────────────────────────────────────────────────────
    ("John 1:1",             ["logos", "word", "jesus", "incarnation"]),
    ("John 1:14",            ["incarnation", "word became flesh", "grace"]),
    ("John 3:16",            ["salvation", "love", "gospel", "eternal life"]),
    ("John 3:36",            ["salvation", "eternal life", "belief"]),
    ("John 8:32",            ["truth", "freedom", "discipleship"]),
    ("John 10:10",           ["life", "abundance", "jesus"]),
    ("John 11:25",           ["resurrection", "life", "jesus"]),
    ("John 13:34-35",        ["love", "commandment", "discipleship"]),
    ("John 14:6",            ["truth", "way", "life", "jesus"]),
    ("John 14:15",           ["love", "obedience", "commandments"]),
    ("John 15:13",           ["love", "sacrifice", "friendship"]),
    ("John 16:33",           ["peace", "tribulation", "overcomer"]),
    # ── Acts ──────────────────────────────────────────────────────────────
    ("Acts 1:8",             ["holy spirit", "witness", "power"]),
    ("Acts 2:38",            ["repentance", "baptism", "holy spirit"]),
    ("Acts 16:31",           ["salvation", "believe", "household"]),
    # ── Romans ────────────────────────────────────────────────────────────
    ("Romans 1:16",          ["gospel", "power", "salvation"]),
    ("Romans 3:23",          ["sin", "fall", "all have sinned"]),
    ("Romans 5:8",           ["love", "atonement", "grace"]),
    ("Romans 6:23",          ["sin", "wages", "gift of god", "eternal life"]),
    ("Romans 8:1",           ["condemnation", "justification", "grace"]),
    ("Romans 8:28",          ["all things", "purpose", "love of god"]),
    ("Romans 8:38-39",       ["love of god", "separation", "nothing can separate"]),
    ("Romans 10:9-10",       ["salvation", "confession", "belief"]),
    ("Romans 12:1-2",        ["transformation", "renewal", "worship"]),
    ("Romans 12:12",         ["hope", "patience", "prayer"]),
    # ── Epistles: Corinthians ──────────────────────────────────────────────
    ("1 Corinthians 10:13",  ["temptation", "faithfulness", "escape"]),
    ("1 Corinthians 13:4-8", ["love", "charity", "agape"]),
    ("1 Corinthians 13:13",  ["faith hope love", "greatest"]),
    ("1 Corinthians 15:3-4", ["gospel", "resurrection", "atonement"]),
    ("2 Corinthians 5:17",   ["new creation", "born again", "transformation"]),
    ("2 Corinthians 5:21",   ["righteousness", "atonement", "exchange"]),
    ("2 Corinthians 12:9",   ["grace", "weakness", "strength"]),
    # ── Galatians ─────────────────────────────────────────────────────────
    ("Galatians 2:20",       ["crucified", "faith", "life in christ"]),
    ("Galatians 5:22-23",    ["fruit of the spirit", "holy spirit"]),
    ("Galatians 6:9",        ["perseverance", "good works", "harvest"]),
    # ── Ephesians ─────────────────────────────────────────────────────────
    ("Ephesians 2:8-9",      ["salvation", "grace", "faith", "works"]),
    ("Ephesians 2:10",       ["good works", "created in christ", "purpose"]),
    ("Ephesians 4:32",       ["forgiveness", "kindness", "love"]),
    ("Ephesians 6:10-18",    ["armor of god", "spiritual warfare", "faith"]),
    # ── Philippians ───────────────────────────────────────────────────────
    ("Philippians 4:4-7",    ["joy", "peace", "prayer", "anxiety"]),
    ("Philippians 4:13",     ["strength", "all things", "christ"]),
    ("Philippians 4:19",     ["provision", "need", "riches"]),
    # ── Colossians ────────────────────────────────────────────────────────
    ("Colossians 3:17",      ["all things", "name of christ", "gratitude"]),
    ("Colossians 3:23",      ["work", "service", "lord"]),
    # ── Thessalonians ─────────────────────────────────────────────────────
    ("1 Thessalonians 5:16-18", ["rejoice", "pray", "thanksgiving"]),
    # ── Timothy ───────────────────────────────────────────────────────────
    ("2 Timothy 1:7",        ["fear", "power", "love", "sound mind"]),
    ("2 Timothy 3:16-17",    ["scripture", "inspiration", "profitable"]),
    # ── Hebrews ───────────────────────────────────────────────────────────
    ("Hebrews 11:1",         ["faith", "hope", "evidence"]),
    ("Hebrews 11:6",         ["faith", "pleasing god", "reward"]),
    ("Hebrews 12:1-2",       ["perseverance", "cloud of witnesses", "jesus"]),
    ("Hebrews 13:5",         ["contentment", "never forsaken", "presence"]),
    # ── James ─────────────────────────────────────────────────────────────
    ("James 1:2-4",          ["trials", "patience", "maturity"]),
    ("James 1:17",           ["good gifts", "father of lights"]),
    ("James 2:17",           ["faith", "works", "dead faith"]),
    ("James 4:7-8",          ["submission", "resist devil", "draw near to god"]),
    # ── Peter ─────────────────────────────────────────────────────────────
    ("1 Peter 2:24",         ["atonement", "healing", "suffering servant"]),
    ("1 Peter 5:7",          ["anxiety", "cast your cares", "god cares"]),
    ("2 Peter 3:9",          ["patience", "repentance", "salvation"]),
    # ── John ──────────────────────────────────────────────────────────────
    ("1 John 1:9",           ["confession", "forgiveness", "cleansing"]),
    ("1 John 4:7-8",         ["love", "god is love", "born of god"]),
    ("1 John 4:19",          ["love", "first loved us"]),
    # ── Revelation ────────────────────────────────────────────────────────
    ("Revelation 3:20",      ["invitation", "knock", "open the door"]),
    ("Revelation 21:4",      ["heaven", "no more tears", "new creation"]),
    ("Revelation 22:13",     ["alpha omega", "jesus", "beginning end"]),
]


def fetch(reference: str, retries: int = 2) -> dict | None:
    url = f"{BASE}/{urllib.parse.quote(reference)}?translation=kjv"
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                data = json.loads(r.read())
            if "error" in data:
                return None
            return data
        except Exception as e:
            if attempt < retries:
                time.sleep(1.0)
            else:
                print(f"  WARN: {reference} → {e}", file=sys.stderr)
    return None


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    corpus = []
    total = len(KEY_VERSES)

    print(f"Fetching {total} passages from bible-api.com …")
    for i, (ref, topics) in enumerate(KEY_VERSES, 1):
        data = fetch(ref)
        if data:
            text = data.get("text", "").strip().replace("\n", " ")
            corpus.append({
                "reference": data.get("reference", ref),
                "text":      text,
                "book":      data.get("verses", [{}])[0].get("book_name", ref.split()[0]),
                "translation": data.get("translation_name", "King James Version"),
                "topics":    topics,
            })
            print(f"  [{i:3}/{total}] ✓  {data.get('reference', ref)}")
        else:
            print(f"  [{i:3}/{total}] ✗  {ref} (skipped)")
        time.sleep(0.4)   # be polite to the free API

    OUT.write_text(json.dumps(corpus, indent=2, ensure_ascii=False))
    print(f"\nSaved {len(corpus)} verses → {OUT}")


if __name__ == "__main__":
    main()
