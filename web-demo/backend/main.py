"""
main.py — iTantra M3 Web Demo FastAPI WebSocket Server
Updated for Semantic Communication + Multi-User Chat
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, Optional
import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import m3_adapter
import translation_engine
import database
import semantic_parser
import semantic_compressor
import semantic_schema
import crypto
import auth
from tinyml_agent import SemanticResult
from chat_router import router as chat_router

logger = logging.getLogger("itantra")

# ── Read env config ────────────────────────────────────────────────────────────
AUTH_MODE = os.getenv("AUTH_MODE", "development")  # 'development' | 'production'

app = FastAPI(title="iTantra M3 Semantic Web Demo")
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400)
database.init_db()

# Include chat router (REST + /ws/chat)
app.include_router(chat_router, prefix="/api")

# Mount static frontend (create placeholder dir if missing)
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(_STATIC_DIR, exist_ok=True)
# Write a minimal index.html placeholder if the dir is empty
_INDEX = os.path.join(_STATIC_DIR, "index.html")
if not os.path.exists(_INDEX):
    with open(_INDEX, "w") as _f:
        _f.write("<!DOCTYPE html><html><body><h1>iTantra Frontend Placeholder</h1></body></html>\n")
app.mount("/static", StaticFiles(directory=_STATIC_DIR, html=True), name="static")


@app.get("/codebook")
def codebook():
    return semantic_schema.get_codebook()


@app.get("/health")
def health():
    """Liveness probe for demo tooling / orchestrators."""
    return {"status": "ok", "service": "itantra-m3-demo", "time": time.time()}


# ──────────────────────────────────────────────────────────────────────────────
# CAPTCHA validation helper
# ──────────────────────────────────────────────────────────────────────────────

def _validate_captcha(captcha_token: str) -> bool:
    """
    Validate a CAPTCHA token.

    Development mode (AUTH_MODE=development):
      - Any non-empty token passes.
      - captcha_token='dev_bypass' also passes with a WARNING logged.
      ⚠️  NEVER use 'dev_bypass' in production — it is a developer shortcut only.

    Production mode: integrate with a real CAPTCHA provider (e.g. hCaptcha, reCAPTCHA).
    """
    if AUTH_MODE != "production":
        if captcha_token == "dev_bypass":
            logger.warning(
                "⚠️  CAPTCHA dev_bypass used — NEVER allow this in production! "
                "Set AUTH_MODE=production and configure CAPTCHA_SECRET_KEY."
            )
        # Accept any token in development
        return bool(captcha_token)

    # Production: validate against CAPTCHA provider
    # TODO: call CAPTCHA_PROVIDER API with CAPTCHA_SECRET_KEY
    raise HTTPException(status_code=501, detail="Production CAPTCHA validation not yet configured")


# ──────────────────────────────────────────────────────────────────────────────
# Auth — Pydantic request/response models
# ──────────────────────────────────────────────────────────────────────────────

class OTPRequest(BaseModel):
    identifier: str
    method: str  # 'phone' | 'email'


class OTPVerifyRequest(BaseModel):
    identifier: str
    otp: str


class SendOTPRequest(BaseModel):
    phone: str
    captcha_token: str


class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str


class SetupProfileRequest(BaseModel):
    token: str
    display_name: str
    preferred_language: str = "en"


class LogoutRequest(BaseModel):
    token: str


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    preferred_language: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Auth endpoints — legacy /auth/* (kept for demo UI compatibility)
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/auth/request-otp")
def request_otp(body: OTPRequest):
    """Request a 6-digit OTP for phone or email authentication.
    Returns otp_for_demo in demo mode (never in production)."""
    try:
        result = auth.generate_otp(body.identifier, body.method)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(
            status_code=429 if "RATE_LIMIT" in str(e) or "RESEND_TOO_SOON" in str(e) else 400,
            detail=str(e)
        )


@app.post("/auth/verify-otp")
def verify_otp_legacy(body: OTPVerifyRequest):
    """Verify a 6-digit OTP. Returns session_token and profile on success."""
    result = auth.verify_otp(body.identifier, body.otp)
    if not result["success"]:
        status = 429 if result["error"] == "TOO_MANY_ATTEMPTS" else 401
        raise HTTPException(status_code=status, detail=result["error"])
    profile = result["profile"]
    return {
        "success": True,
        "session_token": result["session_token"],
        "profile": profile.to_dict() if profile else None,
    }


@app.get("/auth/profile")
def get_profile_endpoint(authorization: Optional[str] = Header(default=None)):
    """Return the authenticated user's profile.
    Requires header: Authorization: Bearer <session_token>"""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    profile = auth.get_profile(token)
    if profile is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    return {"success": True, "profile": profile.to_dict()}


@app.post("/auth/update-profile")
def update_profile_endpoint(body: UpdateProfileRequest, authorization: Optional[str] = Header(default=None)):
    """Update display_name and/or preferred_language for the authenticated user."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    profile = auth.update_profile(token, body.display_name, body.preferred_language)
    if profile is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    return {"success": True, "profile": profile.to_dict()}


# ──────────────────────────────────────────────────────────────────────────────
# Auth endpoints — /api/auth/* (new chat auth flow)
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/api/auth/send-otp")
def api_send_otp(body: SendOTPRequest):
    """
    Send OTP to a phone number.
    Requires a captcha_token (any token in development; real token in production).

    ⚠️  captcha_token='dev_bypass' is accepted in development for testing.
        NEVER use 'dev_bypass' in a production deployment.
    """
    _validate_captcha(body.captcha_token)
    try:
        result = auth.generate_otp(body.phone, "phone")
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(
            status_code=429 if "RATE_LIMIT" in str(e) or "RESEND_TOO_SOON" in str(e) else 400,
            detail=str(e)
        )


@app.post("/api/auth/verify-otp")
def api_verify_otp(body: VerifyOTPRequest):
    """Verify phone OTP. Returns session_token + profile on success."""
    result = auth.verify_otp(body.phone, body.otp)
    if not result["success"]:
        status = 429 if result["error"] == "TOO_MANY_ATTEMPTS" else 401
        raise HTTPException(status_code=status, detail=result["error"])
    profile = result["profile"]
    return {
        "success": True,
        "session_token": result["session_token"],
        "profile": profile.to_dict() if profile else None,
    }


@app.post("/api/auth/setup-profile")
def api_setup_profile(body: SetupProfileRequest):
    """Set display_name and preferred_language after first OTP verification."""
    profile = auth.get_profile(body.token)
    if not profile:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    if body.preferred_language not in translation_engine.SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {body.preferred_language}")
    updated = auth.update_profile(body.token, body.display_name, body.preferred_language)
    if not updated:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    # Mirror into DB
    from database import create_user, get_user_by_phone
    phone = profile.phone or profile.email or profile.id
    if not get_user_by_phone(phone):
        create_user(
            user_id=profile.id,
            phone=phone,
            display_name=body.display_name,
            preferred_language=body.preferred_language,
        )
    else:
        from database import update_user_profile
        update_user_profile(profile.id, body.display_name, body.preferred_language)
    return {"success": True, "profile": updated.to_dict()}


@app.post("/api/auth/logout")
def api_logout(body: LogoutRequest):
    """Invalidate a session token."""
    from auth import _session_store
    _session_store.pop(body.token, None)
    return {"success": True}

connections: Dict[str, WebSocket] = {}
sequence_counters: Dict[str, int] = {"hubbli": 0, "tolankere": 0}
loss_rates: Dict[str, float] = {"hubbli": 0.0, "tolankere": 0.0}
connection_meta: Dict[str, dict] = {}

DEMO_MESSAGES = {
    "hindi":   ("हब्बली में तुरंत एक बचाव दल भेजो", "hi"),
    "english": ("Send one rescue team to Hubbli immediately", "en"),
    "sos":     ("SOS - तत्काल सहायता आवश्यक", "hi"),
}

async def safe_send(ws: Optional[WebSocket], data: dict):
    if ws is None: return
    try: await ws.send_json(data)
    except Exception: pass

async def send_stage(ws: Optional[WebSocket], side: str, stage: str, status: str,
                     duration_ms: float, input_bytes: int = 0, output_bytes: int = 0,
                     details: Optional[dict] = None):
    await safe_send(ws, {
        "type": "stage_update", "side": side, "stage": stage, "status": status,
        "duration_ms": round(duration_ms, 4), "input_bytes": input_bytes,
        "output_bytes": output_bytes, "details": details or {}, "ts": time.time(),
    })

def partner_of(location: str) -> str:
    return "tolankere" if location == "hubbli" else "hubbli"

@app.websocket("/ws/{location}")
async def websocket_endpoint(websocket: WebSocket, location: str):
    if location not in ("hubbli", "tolankere"):
        await websocket.close(code=4001)
        return

    await websocket.accept()
    connections[location] = websocket
    partner = partner_of(location)

    await safe_send(websocket, {
        "type": "connected", "location": location, "partner": partner,
        "partner_connected": partner in connections,
        "adapter_info": m3_adapter.adapter_info(),
        "supported_languages": translation_engine.SUPPORTED_LANGUAGES,
    })

    if partner in connections:
        await safe_send(connections[partner], {"type": "partner_connected", "partner": location})

    try:
        while True:
            raw = await websocket.receive_text()
            try: msg = json.loads(raw)
            except: continue
            await dispatch(location, msg, websocket)
    except WebSocketDisconnect:
        connections.pop(location, None)
        connection_meta.pop(location, None)
        if partner in connections:
            await safe_send(connections[partner], {"type": "partner_disconnected", "partner": location})

async def dispatch(location: str, msg: dict, ws: WebSocket):
    t = msg.get("type", "")
    if t == "set_language":
        connection_meta.setdefault(location, {})["language"] = msg.get("language", "hi")
        await safe_send(ws, {"type": "language_set", "language": msg.get("language")})
    elif t == "send_message":
        await process_send(location, msg, ws)
    elif t == "demo_send":
        preset = msg.get("preset", "hindi")
        text, lang = DEMO_MESSAGES.get(preset, DEMO_MESSAGES["hindi"])
        await process_send(location, {
            "text": text, "language": lang, "callsign": msg.get("callsign", f"{location.upper()[:3]}_01"),
            "priority": 2 if preset == "sos" else 1,
            "target_language": msg.get("target_language", "ta")
        }, ws, is_sos=(preset=="sos"))
    elif t == "trigger_sos":
        await process_send(location, {
            "text": "SOS - तत्काल सहायता आवश्यक", "language": "hi",
            "callsign": msg.get("callsign", f"{location.upper()[:3]}_SOS"),
            "priority": 2, "target_language": msg.get("target_language", "en"),
        }, ws, is_sos=True)
    elif t == "set_loss_rate":
        loss_rates[location] = max(0.0, min(1.0, float(msg.get("rate", 0.0))))
    elif t in ("test_latency", "test_packets", "test_crc", "test_encryption", "corrupt_packet_test"):
        pass # Handle lab tests later
    elif t == "get_system_metrics":
        proc = psutil.Process(os.getpid())
        await safe_send(ws, {
            "type": "system_metrics", "data": {
                "process_cpu_pct": round(proc.cpu_percent(), 2),
                "process_mem_mb": round(proc.memory_info().rss / 1024 / 1024, 2),
                "adapter_mode": m3_adapter.ADAPTER_MODE,
                "stats": database.get_stats()
            }
        })

def _msg_to_tiered_result(msg, text: str, source_lang: str) -> SemanticResult:
    """semantic_parser.SemanticMessage → tiered SemanticResult for compress().

    compress() consumes a SemanticResult (typed enums + a selected
    compression_tier); semantic_parser.parse() returns a SemanticMessage
    (SemanticField values). This maps the parser's richer, multilingual-fixed
    extraction — the same data the SEMANTIC panel displays — onto the wire,
    using the same tier logic as TinyMLAgent:

      TIER_3  parser fell back (free-form)  → original text rides the packet
      TIER_2  anything known (action/entity/condition/location/count/hazard)
      TIER_1  nothing known                 → minimal generic payload

    ENTITY and CONDITION ride in tier2's reserved ctx_flags slot (see
    semantic_compressor.compress_tier2) because SemanticResult has no native
    fields for them, yet the target-language realizers need both.
    """
    from semantic_codebook import ActionCode, UrgencyCode, HazardCode, CompressionTier
    from semantic_schema import Entity as EntityCode, Condition as ConditionCode
    from geo_resolver import GeoResolver

    def _val(field, default=""):
        return str(getattr(field, "value", default) or default).upper()

    # action: parser vocab → ActionCode wire enum (aliases for renamed codes)
    action_val = _val(msg.action, "UNKNOWN")
    _ACTION_ALIAS = {"RESCUE": "RESCUE_REQUEST", "SUPPLY": "SUPPLIES"}
    try:
        action = ActionCode[_ACTION_ALIAS.get(action_val, action_val)]
    except KeyError:
        action = ActionCode.UNKNOWN

    # entity / condition: semantic_schema codes packed into tier2 ctx_flags
    entity_val = _val(msg.entity, "UNKNOWN")
    try:
        entity_code = int(EntityCode[entity_val])
    except KeyError:
        entity_code = 0
    cond_val = _val(msg.condition, "UNKNOWN")
    try:
        condition_code = int(ConditionCode[cond_val])
    except KeyError:
        condition_code = 0

    # urgency: parser vocab → UrgencyCode
    urg_val = _val(msg.urgency, "ROUTINE")
    _URG_ALIAS = {"LOW": "TACTICAL", "MEDIUM": "TACTICAL",
                  "HIGH": "TACTICAL", "CRITICAL": "CRITICAL_SOS"}
    try:
        urgency = UrgencyCode[_URG_ALIAS.get(urg_val, urg_val)]
    except KeyError:
        urgency = UrgencyCode.ROUTINE

    # hazard: free text → HazardCode ("building collapse" → BUILDING_COLLAPSE)
    hz = str(getattr(msg, "hazard_text", "") or "").strip().upper().replace(" ", "_")
    try:
        hazard = HazardCode[hz]
    except KeyError:
        hazard = HazardCode.NONE

    # location: prefer the canonical Target (ASCII, GeoResolver-registered)
    # over proper-noun text; fall back to the raw message.
    target_val = _val(msg.target, "UNKNOWN")
    loc_query = (target_val if target_val not in ("UNKNOWN", "PROPER_LOCATION")
                 else (getattr(msg, "location_text", "") or text))
    loc = GeoResolver.get_instance().resolve_location(loc_query)

    try:
        person_count = max(int(getattr(msg.quantity, "value", 0) or 0), 0)
    except (TypeError, ValueError):
        person_count = 0

    is_fallback = bool(getattr(msg, "is_fallback", False))
    if is_fallback:
        tier = CompressionTier.TIER_3_FALLBACK
    elif (action != ActionCode.UNKNOWN or entity_code or condition_code
          or loc.geo_id != 0 or person_count > 0 or hazard != HazardCode.NONE):
        tier = CompressionTier.TIER_2_STRUCTURED
    else:
        tier = CompressionTier.TIER_1_MACRO

    res = SemanticResult(
        original_text=text,           # TIER_3 passthrough payload
        detected_language=source_lang,
        intent=ActionCode.UNKNOWN,    # reserved; entity/condition use ctx_flags
        action=action,
        hazard=hazard,
        location=loc,
        person_count=person_count,
        urgency=urgency,
        confidence=0.90,
        compression_tier=tier,
        is_fallback=is_fallback,
        fallback_reason=str(getattr(msg, "fallback_reason", "") or ""),
    )
    res.entity = entity_val if entity_code else ""
    res.entity_code = entity_code
    res.condition = cond_val if condition_code else ""
    res.condition_code = condition_code
    return res


async def process_send(location: str, msg: dict, sender_ws: WebSocket, is_sos: bool = False):
    partner = partner_of(location)
    receiver_ws = connections.get(partner)

    text = msg.get("text", "")
    source_lang = msg.get("language", "hi")
    target_lang = msg.get("target_language", "ta")
    callsign = msg.get("callsign", f"{location.upper()[:3]}_01")
    priority = int(msg.get("priority", 0))

    if not text.strip(): return
    sequence_counters[location] = sequence_counters.get(location, 0) + 1
    sequence = sequence_counters[location]
    pipeline_id = f"{location}_{sequence}_{int(time.time()*1000)}"

    total_start = time.perf_counter()
    text_bytes = text.encode('utf-8')

    await safe_send(sender_ws, {"type": "pipeline_start", "side": "sender", "pipeline_id": pipeline_id})
    if receiver_ws: await safe_send(receiver_ws, {"type": "pipeline_start", "side": "receiver", "pipeline_id": pipeline_id})

    # SENDER: STT
    t0 = time.perf_counter()
    stt_ms = (t0 - total_start) * 1000
    await send_stage(sender_ws, "sender", "STT_INPUT", "SUCCESS", stt_ms, 0, len(text_bytes), {"text": text, "lang": source_lang})
    await asyncio.sleep(0.02)

    # SENDER: Semantic Parsing
    t1 = time.perf_counter()
    semantic_msg = semantic_parser.parse(text, source_lang)
    parse_ms = (time.perf_counter() - t1) * 1000
    await send_stage(sender_ws, "sender", "SEMANTIC_PARSING", "SUCCESS", parse_ms, len(text_bytes), 0, {
        "semantic_data": semantic_msg.to_dict(),
        "mode": "MEASURED - Local Regex NLP Model"
    })
    await asyncio.sleep(0.02)

    # SENDER: Semantic Compression
    # compress() consumes a SemanticResult with a selected compression_tier;
    # feeding it the SemanticMessage from semantic_parser.parse() raised
    # AttributeError ('SemanticMessage' has no compression_tier) and tore the
    # WebSocket down mid-pipeline. _msg_to_tiered_result maps the parser's
    # extraction onto the wire so the RX side realizes the same semantics the
    # SEMANTIC panel shows.
    t2 = time.perf_counter()
    tiered_semantic = _msg_to_tiered_result(semantic_msg, text, source_lang)
    semantic_bytes = semantic_compressor.compress(tiered_semantic)
    comp_ms = (time.perf_counter() - t2) * 1000
    await send_stage(sender_ws, "sender", "SEMANTIC_COMPRESSION", "SUCCESS", comp_ms, len(text_bytes), len(semantic_bytes), {
        "output_bytes": len(semantic_bytes),
        "reduction_pct": round(100 * (1 - len(semantic_bytes) / len(text_bytes)), 1),
        "mode": "MEASURED - Semantic Bit-packing"
    })
    await asyncio.sleep(0.02)

    # SENDER: Protobuf Serialization
    t3 = time.perf_counter()
    proto_bytes, proto_fields = m3_adapter.encode_packet(semantic_bytes, source_lang, callsign, sequence, priority)
    proto_ms = (time.perf_counter() - t3) * 1000
    await send_stage(sender_ws, "sender", "PROTOBUF_SERIALIZATION", "SUCCESS", proto_ms, len(semantic_bytes), len(proto_bytes), {
        "mode": f"MEASURED - {m3_adapter.ADAPTER_MODE}"
    })
    await asyncio.sleep(0.02)

    # SENDER: CRC16
    t4 = time.perf_counter()
    crc_val = crypto.calculate_crc16(proto_bytes)
    packet_with_crc = crypto.append_crc16(proto_bytes)
    crc_ms = (time.perf_counter() - t4) * 1000
    await send_stage(sender_ws, "sender", "CRC16", "SUCCESS", crc_ms, len(proto_bytes), len(packet_with_crc), {
        "crc_value": f"0x{crc_val:04X}", "mode": "MEASURED"
    })
    await asyncio.sleep(0.02)

    # SENDER: Encryption
    t5 = time.perf_counter()
    encrypted = crypto.encrypt(packet_with_crc)
    enc_ms = (time.perf_counter() - t5) * 1000
    await send_stage(sender_ws, "sender", "ENCRYPTION", "SUCCESS", enc_ms, len(packet_with_crc), len(encrypted), {
        "algo": "ChaCha20-Poly1305", "mode": "MEASURED"
    })
    await asyncio.sleep(0.02)

    # PACKET READY
    packet_summary = {
        "sequence_number": sequence, "priority": m3_adapter.PRIORITY_NAMES.get(priority, "UNKNOWN"),
        "source_callsign": callsign, "source_language": source_lang, "target_language": target_lang,
        "semantic_payload_bytes": len(semantic_bytes), "crc16": f"0x{crc_val:04X}",
        "encryption": "ChaCha20-Poly1305", "final_packet_bytes": len(encrypted)
    }
    hex_dump = encrypted.hex().upper()
    hex_formatted = ' '.join(hex_dump[i:i+2] for i in range(0, len(hex_dump), 2))
    
    semantic_hex = semantic_bytes.hex().upper()
    semantic_hex_formatted = ' '.join(semantic_hex[i:i+2] for i in range(0, len(semantic_hex), 2))

    await safe_send(sender_ws, {
        "type": "packet_ready", "pipeline_id": pipeline_id, "hex_dump": hex_formatted,
        "packet_fields": packet_summary, "semantic_data": semantic_msg.to_dict(),
        "semantic_binary_hex": semantic_hex_formatted,
        "original_text": text,
        "metrics": {
            "original_text_bytes": len(text_bytes),
            "semantic_payload_bytes": len(semantic_bytes),
            "protobuf_bytes": len(proto_bytes),
            "crc_bytes": len(packet_with_crc),
            "final_packet_bytes": len(encrypted),
            "reduction_pct": round(100 * (1 - len(semantic_bytes) / max(len(text_bytes), 1)), 1),
        }
    })

    # TRANSMISSION
    import random
    dropped = random.random() < loss_rates.get(location, 0.0)
    await send_stage(sender_ws, "sender", "TRANSMISSION", "SUCCESS" if not dropped else "FAILED", 0, len(encrypted), len(encrypted), {
        "transport": "LOCAL DEMO TRANSPORT", "dropped": dropped
    })
    if dropped:
        await safe_send(sender_ws, {"type": "packet_lost", "pipeline_id": pipeline_id, "sequence": sequence})
        if receiver_ws: await safe_send(receiver_ws, {"type": "packet_lost", "from_location": location})
        return
    if not receiver_ws: return

    # RECEIVER: Receive
    recv_start = time.perf_counter()
    await send_stage(receiver_ws, "receiver", "PACKET_RECEIVED", "SUCCESS", 0, len(encrypted), len(encrypted), {"sequence": sequence})
    await asyncio.sleep(0.02)

    # RECEIVER: Decryption
    t6 = time.perf_counter()
    try:
        decrypted = crypto.decrypt(encrypted)
    except Exception as e:
        await send_stage(receiver_ws, "receiver", "DECRYPTION", "FAILED", 0, details={"error": str(e)})
        return
    dec_ms = (time.perf_counter() - t6) * 1000
    await send_stage(receiver_ws, "receiver", "DECRYPTION", "SUCCESS", dec_ms, len(encrypted), len(decrypted), {"mode": "MEASURED"})
    await asyncio.sleep(0.02)

    # RECEIVER: CRC16 Validation
    t7 = time.perf_counter()
    crc_ok, proto_bytes_recv, rcrc, ccrc = crypto.verify_crc16(decrypted)
    crc_verify_ms = (time.perf_counter() - t7) * 1000
    await send_stage(receiver_ws, "receiver", "CRC16_VALIDATION", "SUCCESS" if crc_ok else "FAILED", crc_verify_ms, len(decrypted), len(proto_bytes_recv), {
        "received": f"0x{rcrc:04X}", "computed": f"0x{ccrc:04X}"
    })
    if not crc_ok: return
    await asyncio.sleep(0.02)

    # RECEIVER: Protobuf Decode
    t8 = time.perf_counter()
    try: decoded_packet = m3_adapter.decode_packet(proto_bytes_recv)
    except: return
    decode_ms = (time.perf_counter() - t8) * 1000
    await send_stage(receiver_ws, "receiver", "PROTOBUF_DECODING", "SUCCESS", decode_ms, len(proto_bytes_recv), len(decoded_packet['compressed_payload']), {})
    await asyncio.sleep(0.02)

    # RECEIVER: Semantic Decoding
    t9 = time.perf_counter()
    try: decoded_semantic = semantic_compressor.decompress(decoded_packet['compressed_payload'])
    except: return
    sem_dec_ms = (time.perf_counter() - t9) * 1000
    await send_stage(receiver_ws, "receiver", "SEMANTIC_DECODING", "SUCCESS", sem_dec_ms, len(decoded_packet['compressed_payload']), 0, {
        # entity/condition are dynamic attrs set by decompress_tier2 and are
        # NOT part of SemanticResult.to_dict() — merge them in so the
        # dashboard's SEMANTIC panel shows the same field rows as the sender.
        "semantic_data": {
            **decoded_semantic.to_dict(),
            "entity": getattr(decoded_semantic, "entity", ""),
            "condition": getattr(decoded_semantic, "condition", ""),
        }
    })
    await asyncio.sleep(0.02)

    # RECEIVER: Target Language Realization
    t10 = time.perf_counter()
    translated_text = translation_engine.realize(decoded_semantic, target_lang)
    if getattr(decoded_semantic, "is_fallback", False):
        # Tier 3 is a bounded (~27B) wire fallback, so the decompressed text may
        # be cut at the byte limit. Free-form content is passthrough anyway
        # (same contract as translate()) and the full original is in-band in
        # this delivery payload — show it whole, not as a cut fragment.
        translated_text = text
    trans_ms = (time.perf_counter() - t10) * 1000
    await send_stage(receiver_ws, "receiver", "LANGUAGE_REALIZATION", "SUCCESS", trans_ms, 0, len(translated_text.encode('utf-8')), {
        "translated_text": translated_text, "mode": "MEASURED - Target Realization"
    })
    await asyncio.sleep(0.02)

    # RECEIVER: TTS
    await send_stage(receiver_ws, "receiver", "TTS", "SUCCESS", 0, 0, 0, {"mode": "FALLBACK - Browser Web Speech API"})
    
    total_ms = (time.perf_counter() - total_start) * 1000

    metrics = {
        "original_text_bytes": len(text_bytes),
        "semantic_payload_bytes": len(semantic_bytes),
        "final_packet_bytes": len(encrypted),
        "reduction_pct": round(100 * (1 - len(semantic_bytes) / max(len(text_bytes), 1)), 1),
        "total_latency_ms": round(total_ms, 2)
    }

    delivery_msg = {
        "type": "message_delivered", "pipeline_id": pipeline_id, "from_location": location,
        "to_location": partner, "original_text": text, "translated_text": translated_text,
        "source_language_name": translation_engine.get_language_name(source_lang),
        "target_language_name": translation_engine.get_language_name(target_lang),
        "priority": priority, "callsign": callsign, "is_sos": is_sos or priority == 2,
        "packet_fields": packet_summary, "hex_dump": hex_formatted, "metrics": metrics,
        "semantic_data": decoded_semantic.to_dict(), "timestamp": time.time()
    }

    await safe_send(receiver_ws, delivery_msg)
    await safe_send(sender_ws, {**delivery_msg, "type": "message_sent_confirmed"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, log_level="info")
