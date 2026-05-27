from __future__ import annotations
import logging
from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse, SafetyFlag, ScriptureRef
from app.services import safety_guardian, scripture_service, session_store, llm_service
from app.services.bible_rag import get_rag

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    # ── Stage 1: fast rule-based safety check ──────────────────────────────
    safety = safety_guardian.check_text(req.message)
    if safety and safety.severity == "blocked":
        return ChatResponse(
            response=safety.message,
            safety_flag=safety,
            session_id=req.session_id,
            denomination=req.denomination,
        )

    # ── Stage 2: LLM safety classification for ambiguous cases ────────────
    if safety is None:
        classification = await llm_service.classify_safety(req.message)
        if classification.get("category") not in ("SAFE",) and classification.get("confidence", 0) > 0.75:
            cat = classification["category"].lower()
            redirects = {
                "verse_rewrite": safety_guardian._REDIRECT_MESSAGES.get("verse_rewrite", ""),
                "hateful": safety_guardian._REDIRECT_MESSAGES.get("hateful", ""),
                "extremist": safety_guardian._REDIRECT_MESSAGES.get("extremist", ""),
                "prompt_injection": safety_guardian._REDIRECT_MESSAGES.get("prompt_injection", ""),
                "manipulation": "I want to engage honestly with your question. Let me share what the Bible actually teaches on this topic.",
                "unsafe_image": "I noticed this message involves image content I can't generate. Please use the Image tab for Christian image requests.",
            }
            redirect_msg = redirects.get(cat, "I want to help — could you rephrase your question so I can assist you faithfully?")
            if redirect_msg:
                flag = SafetyFlag(category=cat, severity="blocked", message=redirect_msg)
                return ChatResponse(
                    response=redirect_msg,
                    safety_flag=flag,
                    session_id=req.session_id,
                    denomination=req.denomination,
                )

    # ── Scripture grounding ────────────────────────────────────────────────
    verified_verses, corrections = await scripture_service.ground_message(req.message)

    # Semantic RAG search for topically relevant passages
    rag = get_rag()
    semantic_hits: list[dict] = []
    if rag:
        semantic_hits = rag.search(req.message, top_k=3)

    # ── Generate response ──────────────────────────────────────────────────
    history = session_store.history_as_gemini_messages(req.session_id)

    verified_dicts = [v.model_dump() for v in verified_verses]

    response_text = await llm_service.generate_response(
        user_message=req.message,
        conversation_history=history,
        denomination=req.denomination.value,
        verified_verses=verified_dicts,
        semantic_verses=semantic_hits,
        corrections=corrections,
    )

    # ── Persist turn to session memory ────────────────────────────────────
    session_store.add_turn(req.session_id, req.message, response_text)

    # ── Build scripture reference cards for the UI ─────────────────────────
    scripture_refs = [
        ScriptureRef(reference=v["reference"], text=v["text"], translation=v.get("translation", "KJV"), relevance="direct")
        for v in verified_dicts
    ] + [
        ScriptureRef(reference=s["reference"], text=s["text"], translation=s.get("translation", "KJV"), relevance="semantic")
        for s in semantic_hits
        if s["reference"] not in {v["reference"] for v in verified_dicts}
    ]

    return ChatResponse(
        response=response_text,
        scripture_references=scripture_refs,
        corrections=corrections,
        safety_flag=safety,  # may carry a "warned" flag even if not blocked
        session_id=req.session_id,
        denomination=req.denomination.value,
    )


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    history = session_store.get_history(session_id)
    return {"session_id": session_id, "messages": [m.model_dump() for m in history]}


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    session_store.clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}
