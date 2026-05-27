from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class Denomination(str, Enum):
    CATHOLIC = "catholic"
    PROTESTANT_REFORMED = "protestant_reformed"
    PROTESTANT_EVANGELICAL = "protestant_evangelical"
    PROTESTANT_LUTHERAN = "protestant_lutheran"
    ORTHODOX_EASTERN = "orthodox_eastern"
    PENTECOSTAL = "pentecostal"
    NONDENOMINATIONAL = "nondenominational"


class ScriptureRef(BaseModel):
    reference: str
    text: str
    translation: str = "KJV"
    relevance: str = "semantic"  # "direct" | "semantic"


class SafetyFlag(BaseModel):
    category: str
    severity: str  # "blocked" | "warned" | "redirected"
    message: str


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1, max_length=2000)
    denomination: Denomination = Denomination.NONDENOMINATIONAL


class ChatResponse(BaseModel):
    response: str
    scripture_references: List[ScriptureRef] = []
    corrections: List[str] = []
    safety_flag: Optional[SafetyFlag] = None
    session_id: str
    denomination: str


class ImageRequest(BaseModel):
    session_id: str
    prompt: str = Field(..., min_length=1, max_length=500)
    denomination: Denomination = Denomination.NONDENOMINATIONAL


class ImageResponse(BaseModel):
    image_url: Optional[str] = None
    enhanced_prompt: Optional[str] = None
    safety_flag: Optional[SafetyFlag] = None
    session_id: str


class SessionMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
