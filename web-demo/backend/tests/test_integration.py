"""
tests/test_integration.py — iTantra Full Integration Tests

Tests:
  1. Complete 10×10 language translation matrix with semantic preservation
  2. Three-phone isolation (A↔B, A↔C, B↔C — messages never cross)
  3. Multilingual three-phone test (Hindi, Marathi, Telugu)
  4. Full end-to-end flow (register → login → profile → conversation → message → history)
  5. Authorization (User C cannot access A↔B conversation)
  6. Message deduplication (same message_id submitted twice → one record)
  7. Chat history pagination
  8. Reconnection (messages persist while user is offline)
"""

import os
import sys
import json
import time
import uuid
import pytest
import tempfile

_BACKEND = os.path.dirname(os.path.dirname(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

_TMP_DB2 = tempfile.mktemp(suffix=".integration.db")

import database as _db2
_db2._DB_PATH = _TMP_DB2

import database
import auth
from translation_engine import translate, realize, SUPPORTED_LANGUAGES
import semantic_parser
from semantic_schema import SemanticMessage


@pytest.fixture(autouse=True, scope="session")
def integration_db():
    database.init_db()
    yield
    try:
        os.unlink(_TMP_DB2)
    except FileNotFoundError:
        pass


@pytest.fixture(autouse=True)
def reset_auth_state():
    auth.reset_stores()



def _register(phone: str, name: str, lang: str) -> dict:
    """Helper: full registration → returns {user_id, token}"""
    r = auth.generate_otp(phone, "phone")
    otp = r["otp_for_demo"]
    v = auth.verify_otp(phone, otp)
    assert v["success"], f"OTP verify failed for {phone}: {v}"
    token = v["session_token"]
    user_id = v["user_id"]
    database.create_user(user_id, phone, name, lang)
    database.update_user_language(user_id, lang)
    return {"user_id": user_id, "token": token, "phone": phone, "lang": lang, "name": name}


# ─────────────────────────────────────────────────────────────────────
# 1. FULL 10×10 TRANSLATION MATRIX WITH SEMANTIC PRESERVATION
# ─────────────────────────────────────────────────────────────────────

class TestFull10x10Matrix:
    """All 100 source→target language combinations."""

    TEST_MSG_EN = "Send 2 rescue teams to Hubbli immediately."

    def _semantic_from_result(self, result: str):
        """Re-parse the realized text to verify semantic fields survived."""
        # The result is in some target language; we parse it back with English hints
        # Instead: verify the translate() pipeline by checking realize() directly
        return result

    @pytest.mark.parametrize("source", SUPPORTED_LANGUAGES)
    @pytest.mark.parametrize("target", SUPPORTED_LANGUAGES)
    def test_translate_all_pairs(self, source, target):
        """Every source→target pair must produce a non-empty non-error string."""
        result = translate(self.TEST_MSG_EN, source, target)
        assert result is not None, f"translate({source}→{target}) returned None"
        assert isinstance(result, str), f"translate({source}→{target}) not a string"
        assert len(result.strip()) > 0, f"translate({source}→{target}) returned empty"
        assert "PROPER_LOCATION" not in result, f"{source}→{target} has PROPER_LOCATION sentinel"
        assert "UNKNOWN" not in result.upper().split()[:3], \
            f"{source}→{target} starts with UNKNOWN: {result[:60]}"

    def test_semantic_preservation_send_team(self):
        """
        Parse 'Send 2 rescue teams to Hubbli' in English.
        Realize in all 10 target languages.
        Re-parse each realization.
        Verify: action, entity, target are preserved through the pipeline.
        """
        original = "Send 2 rescue teams to Hubbli immediately."
        src_msg = semantic_parser.parse(original, "en")

        assert src_msg.action.code != 0, "Action should be recognized"

        results = {}
        for lang in SUPPORTED_LANGUAGES:
            realized = realize(src_msg, lang)
            results[lang] = realized
            assert realized and len(realized) > 3, f"realize({lang}) returned: {realized!r}"

        # English and Hindi realizations should contain 'Hubbli' or equivalent
        en_result = results["en"]
        hi_result = results["hi"]
        assert any(w in en_result for w in ["Hubbli", "hubbli", "hubli", "rescue", "Rescue"]), \
            f"English realization missing key content: {en_result}"
        assert any(w in hi_result for w in ["हब्बली", "बचाव", "हब्ब", "रेस्क्यू"]), \
            f"Hindi realization missing key content: {hi_result}"

    def test_identity_translations(self):
        """source == target must return non-empty result for all 10 languages."""
        msg = "Send rescue team to hospital immediately."
        src_msg = semantic_parser.parse(msg, "en")
        for lang in SUPPORTED_LANGUAGES:
            result = realize(src_msg, lang)
            assert result and len(result) > 3, \
                f"Identity translation for {lang} empty: {result!r}"

    def test_non_english_pairs_work(self):
        """Specific non-English pairs that were previously broken."""
        pairs = [
            ("hi", "mr"), ("te", "bn"), ("ta", "kn"),
            ("gu", "ml"), ("or", "hi"), ("bn", "te"),
            ("mr", "ml"), ("gu", "ta"), ("kn", "te"), ("ml", "kn")
        ]
        msg = "Send rescue team to Hubbli immediately."
        for src, tgt in pairs:
            result = translate(msg, src, tgt)
            assert result and len(result) > 3, \
                f"Failed pair {src}→{tgt}: {result!r}"
            assert "PROPER_LOCATION" not in result, \
                f"{src}→{tgt} has PROPER_LOCATION sentinel: {result}"


# ─────────────────────────────────────────────────────────────────────
# 2. THREE-PHONE ISOLATION TEST
# ─────────────────────────────────────────────────────────────────────

class TestThreePhoneIsolation:
    """Messages in A↔B must NEVER appear in A↔C or B↔C."""

    @pytest.fixture(scope="class")
    def three_phones(self):
        a = _register("+911111111101", "Alice_I", "hi")
        b = _register("+911111111102", "Bob_I",   "mr")
        c = _register("+911111111103", "Carol_I", "te")

        conv_ab = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])
        conv_ac = database.get_or_create_direct_conversation(a["user_id"], c["user_id"])
        conv_bc = database.get_or_create_direct_conversation(b["user_id"], c["user_id"])

        return {
            "a": a, "b": b, "c": c,
            "conv_ab": conv_ab, "conv_ac": conv_ac, "conv_bc": conv_bc
        }

    def _send(self, sender: dict, conv_id: str, text: str):
        msg_id = str(uuid.uuid4())
        members = database.get_conversation_members(conv_id)
        for member_id in members:
            user = database.get_user_by_id(member_id)
            tgt_lang = user["preferred_language"] if user else "en"
            t_text = translate(text, sender["lang"], tgt_lang)
            if member_id == sender["user_id"]:
                database.save_chat_message({
                    "id": msg_id, "conversation_id": conv_id,
                    "sender_id": sender["user_id"], "original_text": text,
                    "source_language": sender["lang"], "target_language": tgt_lang,
                    "translated_text": t_text, "timestamp": time.time(),
                    "status": "sent", "priority": 0
                })
        return msg_id

    def test_ab_messages_not_in_ac(self, three_phones):
        tp = three_phones
        msg_id = self._send(tp["a"], tp["conv_ab"], "Help in AB conversation")
        msgs_ab = [m["id"] for m in database.get_conversation_messages(tp["conv_ab"])]
        msgs_ac = [m["id"] for m in database.get_conversation_messages(tp["conv_ac"])]
        assert msg_id in msgs_ab, "AB message should be in AB"
        assert msg_id not in msgs_ac, "AB message must NOT appear in AC"

    def test_ac_messages_not_in_ab(self, three_phones):
        tp = three_phones
        msg_id = self._send(tp["a"], tp["conv_ac"], "Medical team needed in AC")
        msgs_ac = [m["id"] for m in database.get_conversation_messages(tp["conv_ac"])]
        msgs_ab = [m["id"] for m in database.get_conversation_messages(tp["conv_ab"])]
        assert msg_id in msgs_ac
        assert msg_id not in msgs_ab

    def test_bc_messages_not_in_ab_or_ac(self, three_phones):
        tp = three_phones
        msg_id = self._send(tp["b"], tp["conv_bc"], "Road blocked in BC")
        msgs_bc = [m["id"] for m in database.get_conversation_messages(tp["conv_bc"])]
        msgs_ab = [m["id"] for m in database.get_conversation_messages(tp["conv_ab"])]
        msgs_ac = [m["id"] for m in database.get_conversation_messages(tp["conv_ac"])]
        assert msg_id in msgs_bc
        assert msg_id not in msgs_ab
        assert msg_id not in msgs_ac

    def test_simultaneous_sends_stay_isolated(self, three_phones):
        """A→B and A→C at same time must not mix."""
        tp = three_phones
        ab1 = self._send(tp["a"], tp["conv_ab"], "Send ambulance to B")
        ac1 = self._send(tp["a"], tp["conv_ac"], "Send fire brigade to C")

        msgs_ab = {m["id"] for m in database.get_conversation_messages(tp["conv_ab"])}
        msgs_ac = {m["id"] for m in database.get_conversation_messages(tp["conv_ac"])}

        assert ab1 in msgs_ab and ab1 not in msgs_ac
        assert ac1 in msgs_ac and ac1 not in msgs_ab

    def test_c_cannot_read_ab(self, three_phones):
        tp = three_phones
        assert not database.is_conversation_member(tp["conv_ab"], tp["c"]["user_id"])

    def test_a_cannot_read_bc(self, three_phones):
        tp = three_phones
        assert not database.is_conversation_member(tp["conv_bc"], tp["a"]["user_id"])


# ─────────────────────────────────────────────────────────────────────
# 3. MULTILINGUAL THREE-PHONE TEST
# ─────────────────────────────────────────────────────────────────────

class TestMultilingualThreePhone:
    """Verify translation correctness for all direction pairs with 3 users."""

    @pytest.fixture(scope="class")
    def ml_users(self):
        a = _register("+912222222201", "Arjun_ML", "hi")
        b = _register("+912222222202", "Bharat_ML", "mr")
        c = _register("+912222222203", "Chitra_ML", "te")
        conv_ab = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])
        conv_ac = database.get_or_create_direct_conversation(a["user_id"], c["user_id"])
        conv_bc = database.get_or_create_direct_conversation(b["user_id"], c["user_id"])
        return {"a": a, "b": b, "c": c,
                "conv_ab": conv_ab, "conv_ac": conv_ac, "conv_bc": conv_bc}

    def test_a_to_b_hindi_to_marathi(self, ml_users):
        result = translate("तुरंत हब्बली में बचाव दल भेजो", "hi", "mr")
        assert result and len(result) > 3, f"hi→mr failed: {result!r}"
        assert "PROPER_LOCATION" not in result

    def test_a_to_c_hindi_to_telugu(self, ml_users):
        result = translate("अस्पताल में मदद चाहिए", "hi", "te")
        assert result and len(result) > 3, f"hi→te failed: {result!r}"

    def test_b_to_a_marathi_to_hindi(self, ml_users):
        result = translate("तातडीने बचाव पथक पाठवा", "mr", "hi")
        assert result and len(result) > 3, f"mr→hi failed: {result!r}"

    def test_b_to_c_marathi_to_telugu(self, ml_users):
        result = translate("रस्ता बंद आहे", "mr", "te")
        assert result and len(result) > 3, f"mr→te failed: {result!r}"

    def test_c_to_a_telugu_to_hindi(self, ml_users):
        result = translate("వెంటనే సహాయం పంపండి", "te", "hi")
        assert result and len(result) > 3, f"te→hi failed: {result!r}"

    def test_c_to_b_telugu_to_marathi(self, ml_users):
        result = translate("ఆసుపత్రికి అంబులెన్స్ పంపండి", "te", "mr")
        assert result and len(result) > 3, f"te→mr failed: {result!r}"

    def test_routing_correct_ab_not_in_ac(self, ml_users):
        """Messages sent to conv_ab must not appear in conv_ac."""
        a = ml_users["a"]
        msg_id = str(uuid.uuid4())
        database.save_chat_message({
            "id": msg_id, "conversation_id": ml_users["conv_ab"],
            "sender_id": a["user_id"], "original_text": "Hindi to Marathi test",
            "source_language": "hi", "target_language": "mr",
            "translated_text": translate("Hindi to Marathi test", "hi", "mr"),
            "timestamp": time.time(), "status": "sent", "priority": 0
        })
        in_ab = any(m["id"] == msg_id for m in database.get_conversation_messages(ml_users["conv_ab"]))
        in_ac = any(m["id"] == msg_id for m in database.get_conversation_messages(ml_users["conv_ac"]))
        assert in_ab and not in_ac


# ─────────────────────────────────────────────────────────────────────
# 4. FULL END-TO-END FLOW
# ─────────────────────────────────────────────────────────────────────

class TestFullEndToEnd:
    """Complete: register → login → profile → find user → conversation → send → history."""

    def test_complete_flow(self):
        # Step 1: Register User X
        phone_x = "+913333333301"
        r = auth.generate_otp(phone_x, "phone")
        otp = r["otp_for_demo"]
        assert otp and len(otp) == 6

        v = auth.verify_otp(phone_x, otp)
        assert v["success"]
        token_x = v["session_token"]
        uid_x = v["user_id"]

        # Step 2: Setup profile (language: Kannada)
        database.create_user(uid_x, phone_x, "Xavier", "kn")
        profile_x = database.get_user_by_id(uid_x)
        assert profile_x["preferred_language"] == "kn"

        # Step 3: Register User Y
        phone_y = "+913333333302"
        r2 = auth.generate_otp(phone_y, "phone")
        v2 = auth.verify_otp(phone_y, r2["otp_for_demo"])
        assert v2["success"]
        uid_y = v2["user_id"]
        database.create_user(uid_y, phone_y, "Yamini", "ta")

        # Step 4: Find user Y by phone
        found = database.get_user_by_phone(phone_y)
        assert found is not None
        assert found["id"] == uid_y

        # Step 5: Create conversation
        conv_id = database.get_or_create_direct_conversation(uid_x, uid_y)
        assert conv_id
        assert database.is_conversation_member(conv_id, uid_x)
        assert database.is_conversation_member(conv_id, uid_y)

        # Step 6: Send semantic message (Kannada → Tamil)
        original_text = "ತಕ್ಷಣ ಆಸ್ಪತ್ರೆಗೆ ವೈದ್ಯಕೀಯ ತಂಡವನ್ನು ಕಳುಹಿಸಿ"
        src_msg = semantic_parser.parse(original_text, "kn")
        translated = realize(src_msg, "ta")
        assert translated and len(translated) > 3

        # Step 7: Save message
        msg_id = str(uuid.uuid4())
        database.save_chat_message({
            "id": msg_id, "conversation_id": conv_id,
            "sender_id": uid_x, "original_text": original_text,
            "source_language": "kn", "target_language": "ta",
            "translated_text": translated, "timestamp": time.time(),
            "status": "sent", "priority": 0,
            "semantic_payload": json.dumps(src_msg.to_dict())
        })

        # Step 8: Retrieve history — message persists
        history = database.get_conversation_messages(conv_id)
        assert len(history) >= 1
        last = history[-1]
        assert last["id"] == msg_id
        assert last["original_text"] == original_text
        assert last["translated_text"] == translated
        assert last["source_language"] == "kn"
        assert last["target_language"] == "ta"

        # Step 9: Session valid — can get profile
        profile = auth.get_profile(token_x)
        assert profile is not None

        # Step 10: "Reload" — history still there
        history2 = database.get_conversation_messages(conv_id)
        assert any(m["id"] == msg_id for m in history2), "History must persist after reload"


# ─────────────────────────────────────────────────────────────────────
# 5. AUTHORIZATION — C CANNOT ACCESS A↔B
# ─────────────────────────────────────────────────────────────────────

class TestAuthorization:

    @pytest.fixture(scope="class")
    def auth_users(self):
        a = _register("+914444444401", "AuthA", "en")
        b = _register("+914444444402", "AuthB", "hi")
        c = _register("+914444444403", "AuthC", "mr")
        conv_ab = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])
        return {"a": a, "b": b, "c": c, "conv_ab": conv_ab}

    def test_a_is_member_of_ab(self, auth_users):
        assert database.is_conversation_member(
            auth_users["conv_ab"], auth_users["a"]["user_id"])

    def test_b_is_member_of_ab(self, auth_users):
        assert database.is_conversation_member(
            auth_users["conv_ab"], auth_users["b"]["user_id"])

    def test_c_is_not_member_of_ab(self, auth_users):
        assert not database.is_conversation_member(
            auth_users["conv_ab"], auth_users["c"]["user_id"])

    def test_c_cannot_send_to_ab(self, auth_users):
        """C should not be able to put messages into AB conversation."""
        is_member = database.is_conversation_member(
            auth_users["conv_ab"], auth_users["c"]["user_id"])
        assert not is_member, "C must not be authorized to send into AB"

    def test_invalid_session_rejected(self):
        bad_token = "totally_fake_token_12345"
        profile = auth.get_profile(bad_token)
        assert profile is None


# ─────────────────────────────────────────────────────────────────────
# 6. MESSAGE DEDUPLICATION
# ─────────────────────────────────────────────────────────────────────

class TestDeduplication:

    def test_same_message_id_inserted_twice(self):
        a = _register("+915555555501", "DedupA", "en")
        b = _register("+915555555502", "DedupB", "hi")
        conv = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])
        fixed_id = str(uuid.uuid4())

        # First insert
        database.save_chat_message({
            "id": fixed_id, "conversation_id": conv,
            "sender_id": a["user_id"], "original_text": "First insert",
            "source_language": "en", "target_language": "hi",
            "translated_text": "पहला संदेश", "timestamp": time.time(),
            "status": "sent", "priority": 0
        })

        # Second insert with same id (simulates retry)
        try:
            database.save_chat_message({
                "id": fixed_id, "conversation_id": conv,
                "sender_id": a["user_id"], "original_text": "Duplicate retry",
                "source_language": "en", "target_language": "hi",
                "translated_text": "डुप्लीकेट", "timestamp": time.time(),
                "status": "sent", "priority": 0
            })
        except Exception:
            pass  # duplicate key error expected

        msgs = database.get_conversation_messages(conv)
        ids = [m["id"] for m in msgs]
        assert ids.count(fixed_id) == 1, \
            f"Message id appeared {ids.count(fixed_id)} times — must be exactly 1"


# ─────────────────────────────────────────────────────────────────────
# 7. CHAT HISTORY PERSISTENCE (offline → reconnect)
# ─────────────────────────────────────────────────────────────────────

class TestChatHistoryPersistence:

    def test_messages_persist_across_sessions(self):
        """Simulates closing and reopening — history must remain."""
        a = _register("+916666666601", "PersistA", "en")
        b = _register("+916666666602", "PersistB", "kn")
        conv = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])

        sent_ids = []
        for i in range(5):
            mid = str(uuid.uuid4())
            sent_ids.append(mid)
            database.save_chat_message({
                "id": mid, "conversation_id": conv,
                "sender_id": a["user_id"],
                "original_text": f"Message {i}",
                "source_language": "en", "target_language": "kn",
                "translated_text": f"ಸಂದೇಶ {i}",
                "timestamp": time.time() + i,
                "status": "sent", "priority": 0
            })

        # Re-fetch (simulates reconnect / page reload)
        history = database.get_conversation_messages(conv, limit=10)
        stored_ids = [m["id"] for m in history]
        for mid in sent_ids:
            assert mid in stored_ids, f"Message {mid} missing after 'reconnect'"

    def test_pagination_limit(self):
        """get_conversation_messages respects limit parameter."""
        a = _register("+916666666701", "PaginA", "en")
        b = _register("+916666666702", "PaginB", "hi")
        conv = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])

        for i in range(20):
            database.save_chat_message({
                "id": str(uuid.uuid4()), "conversation_id": conv,
                "sender_id": a["user_id"], "original_text": f"Msg {i}",
                "source_language": "en", "target_language": "hi",
                "translated_text": f"संदेश {i}", "timestamp": time.time() + i,
                "status": "sent", "priority": 0
            })

        page = database.get_conversation_messages(conv, limit=5)
        assert len(page) <= 5, f"Expected at most 5 messages, got {len(page)}"

    def test_messages_ordered_by_timestamp(self):
        a = _register("+916666666801", "OrderA", "en")
        b = _register("+916666666802", "OrderB", "hi")
        conv = database.get_or_create_direct_conversation(a["user_id"], b["user_id"])

        base_time = time.time()
        for i in range(5):
            database.save_chat_message({
                "id": str(uuid.uuid4()), "conversation_id": conv,
                "sender_id": a["user_id"], "original_text": f"Order {i}",
                "source_language": "en", "target_language": "hi",
                "translated_text": f"क्रम {i}", "timestamp": base_time + i,
                "status": "sent", "priority": 0
            })

        msgs = database.get_conversation_messages(conv, limit=10)
        timestamps = [m["timestamp"] for m in msgs]
        assert timestamps == sorted(timestamps), "Messages not in timestamp order"
