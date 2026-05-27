import logging
from fastapi import APIRouter
from app.models import ImageRequest, ImageResponse
from app.services import safety_guardian, image_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/generate-image", response_model=ImageResponse)
async def generate_image(req: ImageRequest) -> ImageResponse:
    flag = safety_guardian.check_image_prompt(req.prompt)
    if flag:
        return ImageResponse(safety_flag=flag, session_id=req.session_id)

    enhanced = image_service.enhance_prompt(req.prompt, req.denomination.value)
    image_url = image_service.build_image_url(enhanced)

    # Pre-warm Pollinations.ai so the image is cached before the browser requests it
    ok = await image_service.prefetch_image(image_url)
    if not ok:
        logger.warning(f"Prefetch failed for session {req.session_id}, returning URL anyway")

    logger.info(f"Image ready for session {req.session_id}: {enhanced[:80]}...")

    return ImageResponse(
        image_url=image_url,
        enhanced_prompt=enhanced,
        session_id=req.session_id,
    )
