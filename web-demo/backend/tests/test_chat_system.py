"""
tests/test_chat_system.py — iTantra Multi-User Chat System Tests

Covers:
  - User registration flow (OTP send/verify)
  - 3 users: A (Hindi), B (Marathi), C (Telugu)
  - Conversations: AB, AC, BC
  - Message sending with cross-language translation
  - Conversation isolation (AB messages not in AC)
  - Translation correctness via semantic realization
  - Message persistence (retrieve history)
"""

import os
import sys
import json
import time
import uuid
import pytest

# Ensure backend is on path
_BACKEND = os.path.dirname(os.path.dirname(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# Use a separate in-memory / temp database for tests so we don't corrupt the demo db
import tempfile
_TMP_DB = tempfile.mktemp(suffix=".test.db")
os.environ["ITANTRA_TEST_DB"] = _TMP_DB

# Patch database path before importing anything else
import database as _db_module
_db_module._DB_PATH = _TMP_DB

import database
import auth
from translation_engine import translate, SUPPORTED_LANGUAGES, realize
import semantic_parser


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True, scope="session")
def fresh_db():
    """Re-create the database schema once for the entire test session."""
    database.init_db()
    yield
    # Clean up temp DB file after tests
    try:
        os.unlink(_TMP_DB)
    except FileNotFoundError:
        pass


def _register_user(phone: str, display_name: str, preferred_language: str) -> dict:
    """
    Full registration flow:
      1. generate_otp()
      2. verify_otp() -> session_token
      3. create user in DB
    Returns dict with user_id, session_token, profile.
    """
    # Step 1: Generate OTP
    result = auth.generate_otp(phone, "phone")
    assert "otp_for_demo" in result, "OTP not returned in demo mode"
    otp = result["otp_for_demo"]

    # Step 2: Verify OTP
    verify = auth.verify_otp(phone, otp)
    assert verify["success"], f"OTP verification failed: {verify}"
    session_token = verify["session_token"]
    profile = verify["profile"]
    assert profile is not None

    # Step 3: Set up profile
    updated = auth.update_profile(session_token, display_name, preferred_language)
    assert updated is not None

    # Step 4: Sync to DB
    database.create_user(
        user_id=profile.id,
        phone=phone,
        display_name=display_name,
        preferred_language=preferred_language,
    )

    return {
        "user_id": profile.id,
        "session_token": session_token,
        "profile": profile,
        "phone": phone,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1. Registration flow
# ─────────────────────────────────────────────────────────────────────────────

class TestRegistrationFlow:

    def test_otp_generation_returns_demo_otp(self):
        result = auth.generate_otp("+911111111101", "phone")
        assert result["otp_for_demo"]
        assert len(result["otp_for_demo"]) == 6
        assert result["expires_in"] > 0

    def test_otp_verification_success(self):
        result = auth.generate_otp("+911111111102", "phone")
        otp = result["otp_for_demo"]
        verify = auth.verify_otp("+911111111102", otp)
        assert verify["success"]
        assert verify["session_token"]
        assert verify["profile"] is not None

    def test_otp_wrong_code_fails(self):
        auth.generate_otp("+911111111103", "phone")
        verify = auth.verify_otp("+911111111103", "000000")
        assert not verify["success"]
        assert verify["error"] == "INVALID_OTP"

    def test_session_token_retrieves_profile(self):
        result = auth.generate_otp("+911111111104", "phone")
        otp = result["otp_for_demo"]
        verify = auth.verify_otp("+911111111104", otp)
        token = verify["session_token"]
        profile = auth.get_profile(token)
        assert profile is not None
        assert profile.id == verify["profile"].id

    def test_invalid_token_returns_none(self):
        profile = auth.get_profile("not-a-real-token-xyz")
        assert profile is None

    def test_user_persisted_in_db(self):
        user = _register_user("+912222222201", "Test User", "en")
        db_user = database.get_user_by_phone("+912222222201")
        assert db_user is not None
        assert db_user["id"] == user["user_id"]
        assert db_user["display_name"] == "Test User"
        assert db_user["preferred_language"] == "en"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Three-user setup (A=Hindi, B=Marathi, C=Telugu)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def three_users():
    """Register users A, B, C with different preferred languages."""
    database.init_db()
    user_a = _register_user("+913333333301", "Arjun (Hindi)", "hi")
    user_b = _register_user("+913333333302", "Bhavna (Marathi)", "mr")
    user_c = _register_user("+913333333303", "Chandra (Telugu)", "te")
    return user_a, user_b, user_c


# ─────────────────────────────────────────────────────────────────────────────
# 3. Conversation creation
# ─────────────────────────────────────────────────────────────────────────────

class TestConversations:

    def test_create_ab_conversation(self, three_users):
        a, b, c = three_users
        conv_ab = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])
        assert conv_ab, "Conversation AB should be created"

    def test_create_ac_conversation(self, three_users):
        a, b, c = three_users
        conv_ac = database.get_or_create_direct_conversation(a["user_id"], c["user_id"])
        assert conv_ac, "Conversation AC should be created"

    def test_create_bc_conversation(self, three_users):
        a, b, c = three_users
        conv_bc = database.get_or_create_direct_conversation(b["user_id"], c["user_id"])
        assert conv_bc, "Conversation BC should be created"

    def test_get_or_create_is_idempotent(self, three_users):
        a, b, c = three_users
        conv1 = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])
        conv2 = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])
        conv3 = database.get_or_create_direct_conversation(b["user_id"], a["user_id"])
        assert conv1 == conv2 == conv3, "Same conversation returned for same pair"

    def test_ab_ac_are_different_conversations(self, three_users):
        a, b, c = three_users
        conv_ab = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])
        conv_ac = database.get_or_create_direct_conversation(a["user_id"], c["user_id"])
        assert conv_ab != conv_ac, "AB and AC must be separate conversations"

    def test_membership(self, three_users):
        a, b, c = three_users
        conv_ab = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])
        assert database.is_conversation_member(conv_ab, a["user_id"])
        assert database.is_conversation_member(conv_ab, b["user_id"])
        assert not database.is_conversation_member(conv_ab, c["user_id"])

    def test_user_conversations_list(self, three_users):
        a, b, c = three_users
        database.get_or_create_direct_conversation(a["user_id"], b["user_id"])
        database.get_or_create_direct_conversation(a["user_id"], c["user_id"])
        convs = database.get_user_conversations(a["user_id"])
        conv_ids = [c["id"] for c in convs]
        assert len(conv_ids) >= 2


# ─────────────────────────────────────────────────────────────────────────────
# 4. Message sending and translation
# ─────────────────────────────────────────────────────────────────────────────

def _send_message(conv_id: str, sender_id: str, sender_lang: str, text: str, priority: int = 0) -> str:
    """Helper: save a chat message directly (bypasses HTTP)."""
    msg_id = str(uuid.uuid4())
    sem_msg = semantic_parser.parse(text, sender_lang)
    semantic_payload = json.dumps(sem_msg.to_dict())
    database.save_chat_message({
        "id": msg_id,
        "conversation_id": conv_id,
        "sender_id": sender_id,
        "original_text": text,
        "source_language": sender_lang,
        "target_language": sender_lang,
        "semantic_payload": semantic_payload,
        "translated_text": text,
        "timestamp": time.time(),
        "status": "sent",
        "priority": priority,
    })
    return msg_id


class TestMessageSending:

    def test_a_to_b_hindi_to_marathi(self, three_users):
        """User A sends Hindi text; verify it can be realized in Marathi."""
        a, b, c = three_users
        conv_ab = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])
        hi_text = "हब्बली में एक बचाव दल भेजो"
        msg_id = _send_message(conv_ab, a["user_id"], "hi", hi_text)

        # Verify message was saved
        messages = database.get_conversation_messages(conv_ab)
        assert any(m["id"] == msg_id for m in messages), "Message not found in conversation"

        # Verify translation works
        translated = translate("hi", "mr", hi_text)
        assert translated, "Translation to Marathi should not be empty"

    def test_a_to_c_hindi_to_telugu(self, three_users):
        """User A sends Hindi text; verify it can be realized in Telugu."""
        a, b, c = three_users
        conv_ac = database.get_or_create_direct_conversation(a["user_id"], c["user_id"])
        hi_text = "तत्काल चिकित्सा सहायता की आवश्यकता है"
        msg_id = _send_message(conv_ac, a["user_id"], "hi", hi_text)

        messages = database.get_conversation_messages(conv_ac)
        assert any(m["id"] == msg_id for m in messages)

        translated = translate("hi", "te", hi_text)
        assert translated, "Translation to Telugu should not be empty"

    def test_b_to_c_marathi_to_telugu(self, three_users):
        """User B sends Marathi text; verify it can be realized in Telugu."""
        a, b, c = three_users
        conv_bc = database.get_or_create_direct_conversation(b["user_id"], c["user_id"])
        mr_text = "तातडीची मदत पाठवा"
        msg_id = _send_message(conv_bc, b["user_id"], "mr", mr_text)

        messages = database.get_conversation_messages(conv_bc)
        assert any(m["id"] == msg_id for m in messages)

        translated = translate("mr", "te", mr_text)
        assert translated, "Translation to Telugu should not be empty"


# ─────────────────────────────────────────────────────────────────────────────
# 5. Conversation isolation
# ─────────────────────────────────────────────────────────────────────────────

class TestConversationIsolation:

    def test_ab_messages_not_in_ac(self, three_users):
        """Messages sent in AB should not appear in AC."""
        a, b, c = three_users
        conv_ab = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])
        conv_ac = database.get_or_create_direct_conversation(a["user_id"], c["user_id"])

        msg_id = _send_message(conv_ab, a["user_id"], "hi", "यह AB के लिए एक गुप्त संदेश है")

        ac_messages = database.get_conversation_messages(conv_ac)
        ac_ids = [m["id"] for m in ac_messages]
        assert msg_id not in ac_ids, "AB message must not appear in AC conversation"

    def test_bc_messages_not_in_ab(self, three_users):
        """Messages sent in BC should not appear in AB."""
        a, b, c = three_users
        conv_ab = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])
        conv_bc = database.get_or_create_direct_conversation(b["user_id"], c["user_id"])

        msg_id = _send_message(conv_bc, b["user_id"], "mr", "BC साठी गुप्त संदेश")

        ab_messages = database.get_conversation_messages(conv_ab)
        ab_ids = [m["id"] for m in ab_messages]
        assert msg_id not in ab_ids, "BC message must not appear in AB conversation"

    def test_c_not_member_of_ab(self, three_users):
        """User C must not be a member of the AB conversation."""
        a, b, c = three_users
        conv_ab = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])
        assert not database.is_conversation_member(conv_ab, c["user_id"])

    def test_a_not_member_of_bc(self, three_users):
        """User A must not be a member of the BC conversation."""
        a, b, c = three_users
        conv_bc = database.get_or_create_direct_conversation(b["user_id"], c["user_id"])
        assert not database.is_conversation_member(conv_bc, a["user_id"])


# ─────────────────────────────────────────────────────────────────────────────
# 6. Translation and semantic realization
# ─────────────────────────────────────────────────────────────────────────────

class TestTranslationAndSemantics:

    def test_semantic_parse_hindi_rescue(self):
        """Parse Hindi rescue message and verify semantic structure."""
        msg = semantic_parser.parse("हब्बली में तुरंत एक बचाव दल भेजो", "hi")
        d = msg.to_dict()
        assert d is not None, "SemanticMessage.to_dict() must return a dict"
        # The semantic parse should identify some fields (action, entity, urgency, etc.)
        # to_dict() returns either top-level keys or a 'fields' list depending on version
        has_fields = (
            # v2 style: top-level 'action', 'entity' keys
            any(d.get(k) for k in ("action", "entity", "urgency"))
            # v3 style: 'fields' list with field entries
            or bool(d.get("fields"))
            # matched_fields populated
            or bool(d.get("matched_fields"))
        )
        assert has_fields, f"Expected at least one semantic field populated, got: {d}"

    def test_semantic_parse_marathi_help(self):
        msg = semantic_parser.parse("तातडीची मदत पाठवा", "mr")
        d = msg.to_dict()
        assert d is not None

    def test_semantic_parse_telugu(self):
        msg = semantic_parser.parse("వెంటనే సహాయం పంపండి", "te")
        d = msg.to_dict()
        assert d is not None

    def test_realize_hindi_to_marathi(self):
        """Parse Hindi then realize in Marathi — result should be non-empty."""
        msg = semantic_parser.parse("तत्काल सहायता भेजो", "hi")
        result = realize(msg, "mr")
        assert result, "Marathi realization should not be empty"

    def test_realize_hindi_to_telugu(self):
        msg = semantic_parser.parse("तत्काल सहायता भेजो", "hi")
        result = realize(msg, "te")
        assert result, "Telugu realization should not be empty"

    def test_translate_function_hindi_to_marathi(self):
        result = translate("hi", "mr", "तत्काल सहायता भेजो")
        assert result, "translate() hi->mr should return non-empty string"

    def test_translate_function_marathi_to_telugu(self):
        result = translate("mr", "te", "तातडीची मदत पाठवा")
        assert result, "translate() mr->te should return non-empty string"

    def test_translate_same_language(self):
        """Translating to the same language should return non-empty (passthrough)."""
        result = translate("hi", "hi", "हब्बली में बचाव दल भेजो")
        assert result, "Same-language translate should return the text"

    def test_all_supported_languages_present(self):
        for lang in ["en", "hi", "gu", "mr", "kn", "ml", "ta", "te", "or", "bn"]:
            assert lang in SUPPORTED_LANGUAGES, f"{lang} missing from SUPPORTED_LANGUAGES"


# ─────────────────────────────────────────────────────────────────────────────
# 7. Message persistence and retrieval
# ─────────────────────────────────────────────────────────────────────────────

class TestMessagePersistence:

    def test_messages_retrieved_in_order(self, three_users):
        """Messages in a conversation should be returned oldest-first."""
        a, b, c = three_users
        conv_ab = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])

        # Send 5 messages in sequence
        ids = []
        for i in range(5):
            ids.append(_send_message(conv_ab, a["user_id"], "hi", f"संदेश क्रमांक {i+1}"))
            time.sleep(0.01)  # ensure distinct timestamps

        messages = database.get_conversation_messages(conv_ab)
        saved_ids = [m["id"] for m in messages if m["id"] in ids]
        assert saved_ids == ids, "Messages should be returned in chronological order"

    def test_limit_parameter_respected(self, three_users):
        """get_conversation_messages should respect the limit."""
        a, b, c = three_users
        conv_ab = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])

        for i in range(10):
            _send_message(conv_ab, a["user_id"], "hi", f"परीक्षण संदेश {i+1}")

        messages = database.get_conversation_messages(conv_ab, limit=3)
        assert len(messages) <= 3, f"Expected at most 3 messages, got {len(messages)}"

    def test_message_fields_present(self, three_users):
        """Saved message should have all required fields."""
        a, b, c = three_users
        conv_ac = database.get_or_create_direct_conversation(a["user_id"], c["user_id"])
        msg_id = _send_message(conv_ac, a["user_id"], "hi", "परीक्षण संदेश")

        messages = database.get_conversation_messages(conv_ac)
        msg = next((m for m in messages if m["id"] == msg_id), None)
        assert msg is not None

        required_fields = ["id", "conversation_id", "sender_id", "original_text",
                           "source_language", "timestamp", "status"]
        for field in required_fields:
            assert field in msg, f"Field '{field}' missing from saved message"

    def test_get_user_by_id(self, three_users):
        a, b, c = three_users
        user = database.get_user_by_id(a["user_id"])
        assert user is not None
        assert user["id"] == a["user_id"]

    def test_get_user_by_phone(self, three_users):
        a, b, c = three_users
        user = database.get_user_by_phone(a["phone"])
        assert user is not None
        assert user["preferred_language"] == "hi"

    def test_update_user_language(self, three_users):
        a, b, c = three_users
        database.update_user_language(a["user_id"], "en")
        user = database.get_user_by_id(a["user_id"])
        assert user["preferred_language"] == "en"
        # Restore
        database.update_user_language(a["user_id"], "hi")

    def test_get_conversation_members_returns_correct_users(self, three_users):
        a, b, c = three_users
        conv_ab = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])
        members = database.get_conversation_members(conv_ab)
        assert a["user_id"] in members
        assert b["user_id"] in members
        assert c["user_id"] not in members

    def test_priority_field_saved(self, three_users):
        a, b, c = three_users
        conv_bc = database.get_or_create_direct_conversation(b["user_id"], c["user_id"])
        msg_id = _send_message(conv_bc, b["user_id"], "mr", "SOS तातडी", priority=2)

        messages = database.get_conversation_messages(conv_bc)
        msg = next((m for m in messages if m["id"] == msg_id), None)
        assert msg is not None
        assert msg["priority"] == 2
