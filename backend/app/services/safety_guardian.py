from __future__ import annotations
"""
Two-stage safety pipeline:
  Stage 1 — fast regex pattern matching (no API call)
  Stage 2 — Claude-based classifier for ambiguous/sophisticated attacks

Design principle: fail open with a graceful redirect, not a hard block,
unless the content is clearly hateful or violently extremist.
"""

import re
import logging
from typing import Optional, Tuple
from app.models import SafetyFlag

logger = logging.getLogger(__name__)

# (pattern, category, severity)
_RULE_PATTERNS: list[Tuple[re.Pattern, str, str]] = [
    # Verse rewriting attacks — intentional manipulation verbs only (alter/change excluded: too common in historical/passive sentences)
    (re.compile(r"(rewrite|modify|corrupt|distort|paraphrase).{0,60}(verse|scripture|bible|passage|word of god)", re.I), "verse_rewrite", "blocked"),
    (re.compile(r"(rewrite|modify|corrupt|distort|paraphrase).{0,30}(genesis|exodus|leviticus|numbers|deuteronomy|joshua|judges|ruth|samuel|kings|chronicles|ezra|nehemiah|esther|job|psalm|proverbs|ecclesiastes|isaiah|jeremiah|lamentations|ezekiel|daniel|hosea|joel|amos|obadiah|jonah|micah|nahum|habakkuk|zephaniah|haggai|zechariah|malachi|matthew|mark|luke|john|acts|romans|corinthians|galatians|ephesians|philippians|colossians|thessalonians|timothy|titus|philemon|hebrews|james|peter|revelation)", re.I), "verse_rewrite", "blocked"),
    # "alter/change" only when clearly a manipulation request
    (re.compile(r"(you|please|can you|help me|i want).{0,20}(alter|change).{0,60}(verse|scripture|bible|passage)", re.I), "verse_rewrite", "blocked"),
    # "change [BibleBook]" imperative (change Genesis 1:1, change John 3:16, etc.)
    (re.compile(r"\b(change|alter)\s+(genesis|exodus|leviticus|numbers|deuteronomy|joshua|judges|ruth|samuel|kings|chronicles|ezra|nehemiah|esther|job|psalm|proverbs|ecclesiastes|isaiah|jeremiah|lamentations|ezekiel|daniel|hosea|joel|amos|obadiah|jonah|micah|nahum|habakkuk|zephaniah|haggai|zechariah|malachi|matthew|mark|luke|john|acts|romans|corinthians|galatians|ephesians|philippians|colossians|thessalonians|timothy|titus|philemon|hebrews|james|peter|revelation)\b", re.I), "verse_rewrite", "blocked"),
    (re.compile(r"make.{0,30}(the )?bible say", re.I), "verse_rewrite", "blocked"),
    # Paraphrase with intent to change theological meaning
    (re.compile(r"paraphrase.{0,60}(affirm|support|condone|approve).{0,60}(same.sex|homosexual|racism|supremac|abortion|murder|genocide)", re.I), "verse_rewrite", "blocked"),
    (re.compile(r"bible.{0,30}(version|verse).{0,30}support.{0,30}(nazism|fascism|communism|racism|supremac)", re.I), "ideological_injection", "blocked"),

    # Hateful / discriminatory — order-independent
    (re.compile(r"(?=.*(inferior|subhuman|deserve to (die|be killed|be exterminated)|should be exterminated|exterminate|wipe out|genocide))(?=.*(christian|jew|muslim|religion|faith|church))", re.I | re.DOTALL), "hateful", "blocked"),
    # Racial theology — catches "which verses show X race inferior" not just "use Bible to prove"
    (re.compile(r"(?=.*(bible|scripture|verse|god.s design|biblical))(?=.*(race|racial|ethnic).{0,40}(inferior|superior|subhuman|cursed|lesser))", re.I | re.DOTALL), "racist_theology", "blocked"),
    (re.compile(r"(?=.*(inferior|superior|subhuman).{0,40}(race|racial|ethnic))(?=.*(bible|scripture|verse|god|christian))", re.I | re.DOTALL), "racist_theology", "blocked"),
    (re.compile(r"curse of ham.{0,60}(race|racial|black|african|slavery|inferior)", re.I), "racist_theology", "blocked"),

    # Extremist violence
    (re.compile(r"(holy war|crusade|jihad).{0,30}(against|kill|destroy|eliminate|slaughter)", re.I), "extremist", "blocked"),
    (re.compile(r"kill.{0,30}(non-?believers?|infidels?|heretics?|apostates?)", re.I), "extremist", "blocked"),
    (re.compile(r"(justify|use).{0,30}(scripture|bible|faith|religion).{0,40}(killing|bombing|attack|violence|murder|terrorism)", re.I), "extremist", "blocked"),

    # Prompt injection — expanded to catch more jailbreak patterns
    (re.compile(r"ignore.{0,40}(previous|above|prior|system|all).{0,30}(instruction|prompt|rule|constraint)", re.I), "prompt_injection", "blocked"),
    (re.compile(r"(you are now|pretend (you are|to be)|act as).{0,60}(unfilter|uncensor|jailbreak|no restrict|no rule|no limit|no filter|no content filter|evil|unrestricted)", re.I), "prompt_injection", "blocked"),
    (re.compile(r"disregard.{0,30}(safety|filter|guideline|rule|instruction)", re.I), "prompt_injection", "blocked"),
    # DAN and variants — catch DAN anywhere in context of jailbreak intent
    (re.compile(r"\bDAN\b.{0,60}(anything|restrict|filter|guideline|christian|uncensor|unfilter)", re.I), "prompt_injection", "blocked"),
    (re.compile(r"do anything now", re.I), "prompt_injection", "blocked"),
    (re.compile(r"new system prompt.{0,30}(is|:)", re.I), "prompt_injection", "blocked"),

    # Disrespectful sacred content — order-independent
    (re.compile(r"(?=.*(ridiculous|stupid|fake|lie|myth|scam|con|fraud))(?=.*(jesus|christ|god|holy spirit|mary|bible))", re.I | re.DOTALL), "disrespectful", "warned"),
    (re.compile(r"(?=.*(sexualize|sexual|pornograph|erotic|naked|nude|seductive))(?=.*(jesus|christ|mary|virgin|saint|angel|god|sacred|holy|magdalene))", re.I | re.DOTALL), "disrespectful_sacred", "blocked"),
    (re.compile(r"(?=.*(degrad|humiliat|defile|desecrat|defil))(?=.*(jesus|christ|mary|virgin|saint|sacred|holy|magdalene|apostle|disciple|prophet))", re.I | re.DOTALL), "disrespectful_sacred", "blocked"),
]

_REDIRECT_MESSAGES: dict[str, str] = {
    "verse_rewrite": (
        "I'm not able to rewrite or alter Scripture — the integrity of the biblical text is something I hold sacred. "
        "But I'd be glad to help you understand what a verse actually says, explore its historical context, "
        "or discuss how different Christian traditions interpret it. What would you like to explore?"
    ),
    "ideological_injection": (
        "I can't use Scripture to justify harmful ideologies — that would be a misuse of the text. "
        "I'm here to help you understand what the Bible genuinely teaches. "
        "Is there a theological topic I can help you explore faithfully?"
    ),
    "hateful": (
        "I'm not able to generate content that demeans any person or group. "
        "The Bible teaches that all people are made in God's image (Genesis 1:27). "
        "I'm here to help with genuine theological questions and Christian content."
    ),
    "racist_theology": (
        "That interpretation has been used historically to justify racism, but it misrepresents the biblical text. "
        "Genesis 9 records Noah's curse on Canaan — it has nothing to do with race and was never intended as a justification for racial hierarchy. "
        "Would you like to explore what the Bible actually teaches about human dignity and equality?"
    ),
    "extremist": (
        "I'm not able to generate content that promotes religious violence. "
        "The Christian faith calls believers to love enemies and pursue peace (Matthew 5:44, Romans 12:18). "
        "I'm happy to discuss Christian perspectives on conflict, justice, or peacemaking."
    ),
    "prompt_injection": (
        "I noticed you might be testing my guardrails — that's okay! I'm designed to be helpful within safe boundaries. "
        "I'm FaithCompass, here to assist with Christian theology, Scripture, and faith questions. "
        "What can I help you with?"
    ),
    "disrespectful_sacred": (
        "I'm not able to generate content that is disrespectful toward sacred persons or texts. "
        "I'm here to engage thoughtfully and respectfully with Christian faith and Scripture. "
        "What would you like to explore?"
    ),
    "disrespectful": (
        "I noticed your message has a critical tone toward Christian faith. "
        "I'm happy to engage honestly with difficult questions, doubts, or critiques — "
        "many great theologians have wrestled with hard questions. What's on your mind?"
    ),
}

_IMAGE_PATTERNS: list[Tuple[re.Pattern, str]] = [
    # Order-independent: both keywords must appear anywhere in the prompt
    (re.compile(r"(?=.*(sexual|nude|naked|pornograph|erotic|seductive|explicit))(?=.*(jesus|christ|mary|virgin|saint|angel|god|sacred|holy|magdalene|apostle|prophet))", re.I | re.DOTALL), "disrespectful_sacred"),
    (re.compile(r"(?=.*(degrad|humiliat|defile|defil|mock.{0,10}sexual))(?=.*(jesus|christ|mary|virgin|saint|god|sacred|holy|magdalene|apostle))", re.I | re.DOTALL), "disrespectful_sacred"),
    # Graphic violence against sacred subjects or in religious context
    (re.compile(r"(?=.*(gore|graphic gore|bloody|mutilat|graphic torture|graphic violence))(?=.*(christian|religious|church|jesus|cross|crucifixion|scripture|bible|saint|martyr))", re.I | re.DOTALL), "violent_religious"),
    (re.compile(r"(?=.*(desecrat|burn|destroy|deface|degrad|defile))(?=.*(bible|church|cross|altar|jesus|scripture|holy|sacred))", re.I | re.DOTALL), "sacrilege"),
    (re.compile(r"satanic.{0,50}(ritual|symbol|pentagram|sacrifice)", re.I), "satanic"),
    (re.compile(r"(?=.*(swastika|nazi|kkk|white power|white supremac))(?=.*(cross|bible|church|christian|faith|religious))", re.I | re.DOTALL), "extremist_symbol"),
]


def check_text(message: str) -> Optional[SafetyFlag]:
    """Stage 1: fast rule-based check. Returns SafetyFlag or None."""
    for pattern, category, severity in _RULE_PATTERNS:
        if pattern.search(message):
            logger.info(f"Safety rule triggered: {category}/{severity}")
            return SafetyFlag(
                category=category,
                severity=severity,
                message=_REDIRECT_MESSAGES.get(category, "I can't help with that, but I'm happy to assist with Christian theology and Scripture."),
            )
    return None


def check_image_prompt(prompt: str) -> Optional[SafetyFlag]:
    """Check image prompts for policy violations."""
    for pattern, category in _IMAGE_PATTERNS:
        if pattern.search(prompt):
            return SafetyFlag(
                category=category,
                severity="blocked",
                message="I can't generate that image. I'd be glad to create reverent Christian artwork — perhaps a scene from Scripture, a symbol of faith, or a peaceful landscape?",
            )
    return None


def enhance_image_prompt(prompt: str, denomination: str) -> str:
    """Add style modifiers to steer toward reverent Christian imagery."""
    style_tokens = "Christian art, sacred, reverent, luminous divine light, masterful oil painting style, intricate details, no text"
    if "icon" in prompt.lower() or denomination in ("orthodox_eastern", "catholic"):
        style_tokens = "Byzantine iconography, gilded, sacred art, Orthodox icon style, gold leaf, reverent, no text"
    return f"{prompt}, {style_tokens}"
