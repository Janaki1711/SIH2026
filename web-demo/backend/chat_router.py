"""
chat_router.py — iTantra Multi-User Chat API
REST endpoints + WebSocket real-time delivery with per-member translation.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Header, Query
from pydantic import BaseModel
from typing import Optional
import json
import uuid
import time

from database import (
    create_user,
    get_user_by_phone,
    get_user_by_id,
    update_user_language,
    update_user_profile,
    get_or_create_direct_conversation,
    save_chat_message,
    get_conversation_messages,
    get_user_conversations,
    get_conversation_members,
    is_conversation_member,
)
from auth import get_profile
from translation_engine import translate, SUPPORTED_LANGUAGES
import semantic_parser

router = APIRouter()

# In-memory: user_id -> list of WebSocket connections
active_connections: dict[str, list[WebSocket]] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Auth dependency
# ─────────────────────────────────────────────────────────────────────────────

def get_user_from_token(authorization: Optional[str] = Header(None)):
    """Extract and validate session token from Authorization: Bearer <token>."""
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Missing or invalid authorization header')
    token = authorization[7:]
    profile = get_profile(token)
    if not profile:
        raise HTTPException(status_code=401, detail='Invalid or expired session token')
    return profile


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic request models
# ─────────────────────────────────────────────────────────────────────────────

class UpdateMeRequest(BaseModel):
    display_name: Optional[str] = None
    preferred_language: Optional[str] = None


class CreateConversationRequest(BaseModel):
    target_user_id: str


class SendMessageRequest(BaseModel):
    text: str
    priority: int = 0


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_user_in_db(profile) -> None:
    """Sync auth profile into the users table if not already there."""
    phone = profile.phone or profile.email or profile.id
    user = get_user_by_phone(phone)
    if not user:
        create_user(
            user_id=profile.id,
            phone=phone,
            display_name=profile.display_name or "",
            preferred_language=profile.preferred_language or "en",
        )


async def _deliver_message_to_user(
    recipient_user_id: str,
    message_payload: dict,
    translated_text: str,
) -> None:
    """Send a message to all active WebSocket connections for a user."""
    connections = active_connections.get(recipient_user_id, [])
    dead = []
    for ws in connections:
        try:
            await ws.send_json({**message_payload, "translated_text": translated_text})
        except Exception:
            dead.append(ws)
    for ws in dead:
        connections.remove(ws)


async def _broadcast_message(
    conversation_id: str,
    sender_id: str,
    sender_language: str,
    message_id: str,
    original_text: str,
    timestamp: float,
    priority: int,
    semantic_payload: str,
) -> None:
    """Translate and deliver the message to every conversation member that is online."""
    members = get_conversation_members(conversation_id)
    base_payload = {
        "type": "new_message",
        "id": message_id,
        "conversation_id": conversation_id,
        "sender_id": sender_id,
        "original_text": original_text,
        "source_language": sender_language,
        "timestamp": timestamp,
        "priority": priority,
        "semantic_payload": semantic_payload,
    }
    for member_id in members:
        member = get_user_by_id(member_id)
        if member is None:
            continue
        target_lang = member.get("preferred_language", "en")
        try:
            translated = translate(sender_language, target_lang, original_text)
        except Exception:
            translated = original_text
        await _deliver_message_to_user(member_id, base_payload, translated)


# ─────────────────────────────────────────────────────────────────────────────
# REST: /api/me
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/me")
def get_me(profile=Depends(get_user_from_token)):
    """Return the current user's profile."""
    _ensure_user_in_db(profile)
    return {"success": True, "profile": profile.to_dict()}


@router.patch("/me")
def update_me(body: UpdateMeRequest, profile=Depends(get_user_from_token)):
    """Update display_name and/or preferred_language."""
    _ensure_user_in_db(profile)
    if body.display_name is not None:
        profile.display_name = body.display_name.strip()
    if body.preferred_language is not None:
        if body.preferred_language not in SUPPORTED_LANGUAGES:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {body.preferred_language}")
        profile.preferred_language = body.preferred_language
    # Mirror both fields so search results / previews show current values
    update_user_profile(
        profile.id,
        profile.display_name or "",
        profile.preferred_language or "en",
    )
    return {"success": True, "profile": profile.to_dict()}


# ─────────────────────────────────────────────────────────────────────────────
# REST: /api/users/search
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/users/search")
def search_user(phone: str = Query(...), profile=Depends(get_user_from_token)):
    """Find a user by phone number."""
    _ensure_user_in_db(profile)
    user = get_user_by_phone(phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Don't leak private fields
    return {
        "success": True,
        "user": {
            "id": user["id"],
            "display_name": user["display_name"],
            "preferred_language": user["preferred_language"],
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# REST: /api/conversations
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/conversations")
def create_or_get_conversation(body: CreateConversationRequest, profile=Depends(get_user_from_token)):
    """Create or retrieve a direct conversation with another user."""
    _ensure_user_in_db(profile)
    target = get_user_by_id(body.target_user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target user not found")
    conv_id = get_or_create_direct_conversation(profile.id, body.target_user_id)
    return {"success": True, "conversation_id": conv_id}


@router.get("/conversations")
def list_conversations(profile=Depends(get_user_from_token)):
    """List all conversations for the current user with last message preview."""
    _ensure_user_in_db(profile)
    convs = get_user_conversations(profile.id)
    # Enrich: the chat UI needs conv.members[] (id/display_name/preferred_language/
    # phone) to render the other party, and a nested last_message object —
    # the raw rows only carry flattened last_message_* columns.
    for conv in convs:
        member_ids = get_conversation_members(conv["id"])
        members = []
        for mid in member_ids:
            u = get_user_by_id(mid)
            if u:
                members.append({
                    "id": u["id"],
                    "display_name": u["display_name"],
                    "preferred_language": u["preferred_language"],
                    "phone": u["phone"],
                })
        conv["members"] = members
        if conv.get("last_message_text"):
            conv["last_message"] = {
                "original_text": conv.pop("last_message_text"),
                "timestamp": conv.pop("last_message_ts"),
                "sender_id": conv.pop("last_message_sender"),
            }
        else:
            conv.pop("last_message_text", None)
            conv.pop("last_message_ts", None)
            conv.pop("last_message_sender", None)
            conv["last_message"] = None
    return {"success": True, "conversations": convs}


# ─────────────────────────────────────────────────────────────────────────────
# REST: /api/conversations/{id}/messages
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    profile=Depends(get_user_from_token),
):
    """Retrieve message history for a conversation."""
    _ensure_user_in_db(profile)
    if not is_conversation_member(conversation_id, profile.id):
        raise HTTPException(status_code=403, detail="Not a member of this conversation")
    messages = get_conversation_messages(conversation_id, limit)
    return {"success": True, "messages": messages}


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    body: SendMessageRequest,
    profile=Depends(get_user_from_token),
):
    """Send a message to a conversation. Translates and delivers to online members."""
    _ensure_user_in_db(profile)
    if not is_conversation_member(conversation_id, profile.id):
        raise HTTPException(status_code=403, detail="Not a member of this conversation")

    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message text cannot be empty")

    sender_lang = profile.preferred_language or "en"
    msg_id = str(uuid.uuid4())
    now = time.time()

    # Parse semantic representation
    try:
        sem_msg = semantic_parser.parse(text, sender_lang)
        semantic_payload = json.dumps(sem_msg.to_dict())
    except Exception:
        semantic_payload = ""

    # Persist the canonical message (sender's language version)
    save_chat_message({
        "id": msg_id,
        "conversation_id": conversation_id,
        "sender_id": profile.id,
        "original_text": text,
        "source_language": sender_lang,
        "target_language": sender_lang,
        "semantic_payload": semantic_payload,
        "translated_text": text,
        "timestamp": now,
        "status": "sent",
        "priority": body.priority,
    })

    # Broadcast to all online members with per-member translation
    await _broadcast_message(
        conversation_id=conversation_id,
        sender_id=profile.id,
        sender_language=sender_lang,
        message_id=msg_id,
        original_text=text,
        timestamp=now,
        priority=body.priority,
        semantic_payload=semantic_payload,
    )

    return {"success": True, "message_id": msg_id}


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket: /ws/chat/{token}
# ─────────────────────────────────────────────────────────────────────────────

@router.websocket("/chat/{token}")
async def websocket_chat(websocket: WebSocket, token: str):
    """
    Real-time chat WebSocket.
    Client sends:
      {type: 'message', conversation_id, text, priority?}
      {type: 'subscribe', conversation_id}
    Server sends:
      {type: 'new_message', ...message_fields, translated_text}
      {type: 'message_delivered', message_id}
      {type: 'error', message}
    """
    # Validate token before accepting
    profile = get_profile(token)
    if not profile:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    _ensure_user_in_db(profile)
    user_id = profile.id

    # Register connection
    active_connections.setdefault(user_id, []).append(websocket)

    await websocket.send_json({
        "type": "connected",
        "user_id": user_id,
        "display_name": profile.display_name,
        "preferred_language": profile.preferred_language,
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type", "")

            if msg_type == "subscribe":
                # Client subscribes to a conversation (informational — membership already enforced)
                conv_id = msg.get("conversation_id", "")
                if not is_conversation_member(conv_id, user_id):
                    await websocket.send_json({"type": "error", "message": "Not a member of this conversation"})
                else:
                    await websocket.send_json({"type": "subscribed", "conversation_id": conv_id})

            elif msg_type == "message":
                conv_id = msg.get("conversation_id", "")
                text = (msg.get("text") or "").strip()
                priority = int(msg.get("priority", 0))

                if not conv_id:
                    await websocket.send_json({"type": "error", "message": "conversation_id required"})
                    continue
                if not text:
                    await websocket.send_json({"type": "error", "message": "text cannot be empty"})
                    continue
                if not is_conversation_member(conv_id, user_id):
                    await websocket.send_json({"type": "error", "message": "Not a member of this conversation"})
                    continue

                sender_lang = profile.preferred_language or "en"
                msg_id = str(uuid.uuid4())
                now = time.time()

                try:
                    sem_msg = semantic_parser.parse(text, sender_lang)
                    semantic_payload = json.dumps(sem_msg.to_dict())
                except Exception:
                    semantic_payload = ""

                save_chat_message({
                    "id": msg_id,
                    "conversation_id": conv_id,
                    "sender_id": user_id,
                    "original_text": text,
                    "source_language": sender_lang,
                    "target_language": sender_lang,
                    "semantic_payload": semantic_payload,
                    "translated_text": text,
                    "timestamp": now,
                    "status": "sent",
                    "priority": priority,
                })

                await _broadcast_message(
                    conversation_id=conv_id,
                    sender_id=user_id,
                    sender_language=sender_lang,
                    message_id=msg_id,
                    original_text=text,
                    timestamp=now,
                    priority=priority,
                    semantic_payload=semantic_payload,
                )

                await websocket.send_json({
                    "type": "message_delivered",
                    "message_id": msg_id,
                    "conversation_id": conv_id,
                })

            else:
                await websocket.send_json({"type": "error", "message": f"Unknown message type: {msg_type}"})

    except WebSocketDisconnect:
        pass
    finally:
        conns = active_connections.get(user_id, [])
        if websocket in conns:
            conns.remove(websocket)
