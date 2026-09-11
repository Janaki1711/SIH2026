# auth.py — OTP Authentication for iTantra
# Supports phone number or email with 6-digit OTP
# For demo/SIH: uses in-memory store (no external SMS/email service required)
# Production would replace _send_otp_to_phone/_send_otp_to_email with real providers

import secrets
import hashlib
import time
from typing import Optional, Dict, List
from dataclasses import dataclass, field

OTP_EXPIRY_SECONDS = 300        # 5 minutes
OTP_MAX_ATTEMPTS = 3
OTP_RESEND_COOLDOWN = 30        # seconds
OTP_RATE_LIMIT_WINDOW = 3600    # 1 hour
OTP_RATE_LIMIT_MAX = 5          # max OTPs per hour per identifier

# Shared in-memory salt (per process lifetime — fine for demo)
_SALT = secrets.token_hex(16)

# In-memory stores (would be Redis / DB in production)
_otp_store: Dict[str, "OTPRecord"] = {}
_rate_store: Dict[str, List[float]] = {}  # identifier → list of request timestamps
_user_store: Dict[str, "UserProfile"] = {}  # identifier → UserProfile
_session_store: Dict[str, str] = {}  # session_token → identifier


@dataclass
class OTPRecord:
    identifier: str   # phone or email
    otp_hash: str     # SHA-256 of the OTP (never store plaintext)
    created_at: float
    expires_at: float
    attempts: int = 0
    verified: bool = False


@dataclass
class UserProfile:
    id: str
    phone: Optional[str] = None
    email: Optional[str] = None
    display_name: str = ""
    preferred_language: str = "en"
    created_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    session_token: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "phone": self.phone,
            "email": self.email,
            "display_name": self.display_name,
            "preferred_language": self.preferred_language,
            "created_at": self.created_at,
            "last_seen": self.last_seen,
            # Never expose session_token in profile serialization
        }


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _hash_otp(otp: str, identifier: str) -> str:
    """SHA-256(otp + identifier + salt).  Never log OTP values."""
    raw = f"{otp}{identifier}{_SALT}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _check_rate_limit(identifier: str) -> bool:
    """Return True if request is allowed, False if rate-limit exceeded."""
    now = time.time()
    window_start = now - OTP_RATE_LIMIT_WINDOW
    timestamps = _rate_store.get(identifier, [])
    # Drop expired entries
    timestamps = [t for t in timestamps if t >= window_start]
    _rate_store[identifier] = timestamps
    return len(timestamps) < OTP_RATE_LIMIT_MAX


def _record_request(identifier: str) -> None:
    _rate_store.setdefault(identifier, []).append(time.time())


def _can_resend(identifier: str) -> bool:
    """Return True if enough time has passed since last OTP was issued."""
    record = _otp_store.get(identifier)
    if record is None:
        return True
    return (time.time() - record.created_at) >= OTP_RESEND_COOLDOWN


def _send_otp_to_phone(phone: str, otp: str) -> None:
    """Stub — replace with Twilio / AWS SNS / etc. in production.
    NEVER log the otp value in production."""
    pass  # Demo: OTP is returned in the response directly


def _send_otp_to_email(email: str, otp: str) -> None:
    """Stub — replace with SES / SMTP in production.
    NEVER log the otp value in production."""
    pass  # Demo: OTP is returned in the response directly


def _get_or_create_profile(identifier: str, method: str) -> "UserProfile":
    """Return existing profile or create a new one for this identifier."""
    if identifier in _user_store:
        return _user_store[identifier]
    user_id = secrets.token_urlsafe(12)
    profile = UserProfile(
        id=user_id,
        phone=identifier if method == "phone" else None,
        email=identifier if method == "email" else None,
    )
    _user_store[identifier] = profile
    return profile


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_otp(identifier: str, method: str) -> dict:
    """Generate and (demo-)return a 6-digit OTP for the given identifier.

    Args:
        identifier: Phone number (E.164) or email address.
        method:     'phone' or 'email'.

    Returns:
        dict with keys:
          - otp_for_demo: the plaintext OTP (DEMO ONLY — remove in production)
          - expires_in: seconds until OTP expires
          - resend_after: seconds until a new OTP can be requested

    Raises:
        ValueError: on rate-limit violation or invalid method.
    """
    if method not in ("phone", "email"):
        raise ValueError("method must be 'phone' or 'email'")

    if not identifier or not identifier.strip():
        raise ValueError("identifier must be a non-empty string")

    identifier = identifier.strip()

    # Rate limit check
    if not _check_rate_limit(identifier):
        raise ValueError(
            f"RATE_LIMIT_EXCEEDED: max {OTP_RATE_LIMIT_MAX} OTPs per "
            f"{OTP_RATE_LIMIT_WINDOW // 60} minutes"
        )

    # Resend cooldown check
    if not _can_resend(identifier):
        existing = _otp_store.get(identifier)
        resend_in = max(0, OTP_RESEND_COOLDOWN - (time.time() - existing.created_at))
        raise ValueError(
            f"RESEND_TOO_SOON: wait {int(resend_in) + 1} seconds before requesting a new OTP"
        )

    # Generate a cryptographically secure 6-digit OTP
    otp = f"{secrets.randbelow(1_000_000):06d}"
    now = time.time()
    record = OTPRecord(
        identifier=identifier,
        otp_hash=_hash_otp(otp, identifier),
        created_at=now,
        expires_at=now + OTP_EXPIRY_SECONDS,
    )
    _otp_store[identifier] = record
    _record_request(identifier)

    # Dispatch (stubs for demo)
    if method == "phone":
        _send_otp_to_phone(identifier, otp)
    else:
        _send_otp_to_email(identifier, otp)

    return {
        # ⚠️  DEMO ONLY — never include OTP in response in production
        "otp_for_demo": otp,
        "expires_in": OTP_EXPIRY_SECONDS,
        "resend_after": OTP_RESEND_COOLDOWN,
    }


def verify_otp(identifier: str, otp_input: str) -> dict:
    """Verify a 6-digit OTP for the given identifier.

    Returns:
        dict with keys:
          - success: bool
          - error: None | 'INVALID_OTP' | 'OTP_EXPIRED' | 'TOO_MANY_ATTEMPTS' | 'NOT_FOUND'
          - profile: UserProfile | None  (present when success=True)
          - session_token: str | None    (present when success=True)
    """
    identifier = (identifier or "").strip()
    otp_input  = (otp_input  or "").strip()

    record = _otp_store.get(identifier)
    if record is None:
        return {"success": False, "error": "NOT_FOUND", "profile": None, "session_token": None}

    if record.attempts >= OTP_MAX_ATTEMPTS:
        return {"success": False, "error": "TOO_MANY_ATTEMPTS", "profile": None, "session_token": None}

    if time.time() > record.expires_at:
        return {"success": False, "error": "OTP_EXPIRED", "profile": None, "session_token": None}

    # Constant-time comparison via hashing (avoids timing side-channels)
    record.attempts += 1
    expected_hash = record.otp_hash
    provided_hash = _hash_otp(otp_input, identifier)

    if not secrets.compare_digest(expected_hash, provided_hash):
        return {"success": False, "error": "INVALID_OTP", "profile": None, "session_token": None}

    # Success — mark verified and issue session token
    record.verified = True
    session_token = secrets.token_urlsafe(32)

    # Determine method from stored record (phone has no @, email has @)
    method = "email" if "@" in identifier else "phone"
    profile = _get_or_create_profile(identifier, method)
    profile.session_token = session_token
    profile.last_seen = time.time()
    _session_store[session_token] = identifier

    return {
        "success": True,
        "error": None,
        "profile": profile,
        "session_token": session_token,
    }


def get_profile(session_token: str) -> Optional["UserProfile"]:
    """Return the UserProfile associated with a session token, or None."""
    if not session_token:
        return None
    identifier = _session_store.get(session_token)
    if not identifier:
        return None
    profile = _user_store.get(identifier)
    if profile:
        profile.last_seen = time.time()
    return profile


def update_profile(
    session_token: str,
    display_name: Optional[str] = None,
    preferred_language: Optional[str] = None,
) -> Optional["UserProfile"]:
    """Update mutable profile fields. Returns updated profile or None if token invalid."""
    profile = get_profile(session_token)
    if profile is None:
        return None
    if display_name is not None:
        profile.display_name = display_name.strip()
    if preferred_language is not None:
        from translation_engine import SUPPORTED_LANGUAGES
        if preferred_language in SUPPORTED_LANGUAGES:
            profile.preferred_language = preferred_language
    return profile
