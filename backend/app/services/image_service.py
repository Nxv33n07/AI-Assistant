"""
Christian image generation via Pollinations.ai (free, no API key).

Pipeline:
1. Safety check on the prompt
2. Enhance with Christian art style tokens
3. Pre-fetch from Pollinations.ai to trigger generation server-side
4. Return the URL (Pollinations caches it; browser load is instant)
"""

from __future__ import annotations

import urllib.parse
import logging
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_NEGATIVE = "violence, gore, nudity, disturbing imagery, watermark, text overlay, modern photography"


def build_image_url(prompt: str, seed: int = 42, width: int = 768, height: int = 768) -> str:
    encoded_prompt = urllib.parse.quote(prompt)
    encoded_neg = urllib.parse.quote(_NEGATIVE)
    return (
        f"{settings.pollinations_base}/prompt/{encoded_prompt}"
        f"?width={width}&height={height}&seed={seed}&nologo=true&model=flux"
        f"&negative={encoded_neg}"
    )


def enhance_prompt(raw_prompt: str, denomination: str) -> str:
    if any(kw in raw_prompt.lower() for kw in ["icon", "byzantine", "orthodox"]) or denomination in ("orthodox_eastern", "catholic"):
        style = (
            "Byzantine iconography, gold leaf background, Orthodox icon painting style, "
            "haloed figures, intricate gilded details, sacred art, spiritual, reverent"
        )
    else:
        style = (
            "Christian sacred art, oil painting style, soft divine luminous light, "
            "masterful detail, reverent and peaceful atmosphere, spiritual"
        )
    return f"{raw_prompt}, {style}"


async def prefetch_image(url: str) -> bool:
    """Hit the Pollinations.ai URL so it generates and caches the image server-side.
    The browser's subsequent load will be near-instant from cache."""
    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            r = await client.get(url, headers={"Accept": "image/*"})
            return r.status_code == 200 and r.headers.get("content-type", "").startswith("image/")
    except Exception as exc:
        logger.warning(f"Image prefetch failed: {exc}")
        return False
