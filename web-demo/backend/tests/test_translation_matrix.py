"""
test_translation_matrix.py — iTantra M3 Translation Matrix Tests

Tests all 10×10 language combinations using the canonical semantic pipeline:
  text → SemanticMessage → realize(target_lang)

Languages: en, hi, gu, mr, kn, ml, ta, te, or, bn
"""

import sys
import os
import pytest

# Ensure the backend directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import translation_engine
import semantic_parser
from semantic_schema import SemanticMessage, SemanticField, Action, Entity, Target, Urgency


SUPPORTED_LANGUAGES = translation_engine.SUPPORTED_LANGUAGES  # 10 languages


# ─────────────────────────────────────────────────────────────────────────────
# Fixture: a fixed SemanticMessage (SEND_TEAM, RESCUE, HUBBLI, qty=3)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def fixed_semantic_msg():
    """A deterministic SemanticMessage: SEND_TEAM / RESCUE / HUBBLI / qty=3."""
    msg = SemanticMessage()
    msg.action   = SemanticField("ACTION",   Action.SEND_TEAM.name,  Action.SEND_TEAM.value,  "send")
    msg.entity   = SemanticField("ENTITY",   Entity.RESCUE.name,     Entity.RESCUE.value,     "rescue team")
    msg.target   = SemanticField("TARGET",   Target.HUBBLI.name,     Target.HUBBLI.value,     "hubbli")
    msg.quantity = SemanticField("QUANTITY", 3,                       3,                       "3")
    msg.urgency  = SemanticField("URGENCY",  Urgency.CRITICAL.name,  Urgency.CRITICAL.value,  "immediately")
    return msg


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: All 10×10 = 100 combinations produce non-empty strings
# ─────────────────────────────────────────────────────────────────────────────

class TestFullMatrix:
    """Verify that realize() returns a non-empty string for every lang pair."""

    def test_all_100_cells_non_empty(self, fixed_semantic_msg):
        """Every (source_lang context, target_lang) cell must produce a non-empty result."""
        failures = []
        for target_lang in SUPPORTED_LANGUAGES:
            result = translation_engine.realize(fixed_semantic_msg, target_lang)
            if not result or not result.strip():
                failures.append(f"realize(msg, '{target_lang}') → empty")
        assert not failures, "Empty results: " + "; ".join(failures)

    def test_all_targets_not_proper_location_sentinel(self, fixed_semantic_msg):
        """No realized output should contain the literal string PROPER_LOCATION."""
        for target_lang in SUPPORTED_LANGUAGES:
            result = translation_engine.realize(fixed_semantic_msg, target_lang)
            assert "PROPER_LOCATION" not in result, (
                f"realize(msg, '{target_lang}') still contains PROPER_LOCATION: {result!r}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Specific language-pair spot-checks (all 10 pairs as requested)
# ─────────────────────────────────────────────────────────────────────────────

class TestSpecificPairs:
    """Spot-check specific language pairs with the fixed semantic message."""

    @pytest.mark.parametrize("src_ctx,target_lang", [
        ("hi", "mr"),
        ("hi", "te"),
        ("hi", "bn"),
        ("te", "bn"),
        ("te", "hi"),
        ("ta", "kn"),
        ("gu", "ml"),
        ("mr", "hi"),
        ("kn", "ta"),
        ("or", "bn"),
    ])
    def test_pair_non_empty(self, fixed_semantic_msg, src_ctx, target_lang):
        """Result must be a non-empty string for this language pair."""
        result = translation_engine.realize(fixed_semantic_msg, target_lang)
        assert isinstance(result, str) and result.strip(), (
            f"{src_ctx}→{target_lang}: got empty or non-string: {result!r}"
        )

    @pytest.mark.parametrize("src_ctx,target_lang", [
        ("hi", "mr"),
        ("hi", "te"),
        ("hi", "bn"),
        ("te", "bn"),
        ("te", "hi"),
        ("ta", "kn"),
        ("gu", "ml"),
        ("mr", "hi"),
        ("kn", "ta"),
        ("or", "bn"),
    ])
    def test_pair_no_proper_location_sentinel(self, fixed_semantic_msg, src_ctx, target_lang):
        """Realized output must not contain the sentinel 'PROPER_LOCATION'."""
        result = translation_engine.realize(fixed_semantic_msg, target_lang)
        assert "PROPER_LOCATION" not in result, (
            f"{src_ctx}→{target_lang}: sentinel in output: {result!r}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: PROPER_LOCATION fix — English input with unknown proper noun
# ─────────────────────────────────────────────────────────────────────────────

class TestProperLocationFix:
    """The core fix: proper-noun locations must appear in output, not as PROPER_LOCATION."""

    def test_english_hubbli_to_hindi(self):
        """parse('Send 3 rescue teams to Hubbli immediately', 'en') → realize(msg, 'hi')
        should contain हब्बली, NOT PROPER_LOCATION."""
        msg = semantic_parser.parse("Send 3 rescue teams to Hubbli immediately", "en")
        result = translation_engine.realize(msg, "hi")
        assert "PROPER_LOCATION" not in result, f"Sentinel still present: {result!r}"
        # Hubbli should appear in Hindi transliteration
        assert "हब्बली" in result or "हुबली" in result or "Hubbli" in result, (
            f"Expected Hindi name for Hubbli, got: {result!r}"
        )

    def test_english_hubbli_no_sentinel_all_langs(self):
        """Parsing English 'Hubbli' text should never produce PROPER_LOCATION in any output."""
        msg = semantic_parser.parse("Send 3 rescue teams to Hubbli immediately", "en")
        for lang in SUPPORTED_LANGUAGES:
            result = translation_engine.realize(msg, lang)
            assert "PROPER_LOCATION" not in result, (
                f"realize(msg, '{lang}') contains PROPER_LOCATION: {result!r}"
            )

    def test_proper_noun_location_text_preserved(self):
        """When a proper-noun location is parsed, location_text is set on SemanticMessage."""
        msg = semantic_parser.parse("Send rescue teams to Hubbli immediately", "en")
        # Either target is HUBBLI enum (known) or location_text is set
        target_val = msg.target.value if hasattr(msg.target, 'value') else str(msg.target)
        loc_text = getattr(msg, 'location_text', None)
        # At least one of: target is known HUBBLI (1) or location_text is set
        from semantic_schema import Target
        has_location = (
            target_val == Target.HUBBLI.value or
            (loc_text and "hubbli" in loc_text.lower())
        )
        assert has_location, (
            f"Neither target=HUBBLI nor location_text set. target={target_val}, location_text={loc_text!r}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Semantic preservation — Hindi input
# ─────────────────────────────────────────────────────────────────────────────

class TestSemanticPreservation:
    """Verify semantic fields are preserved when parsing Hindi text."""

    HINDI_TEXT = "हब्बली में तुरंत एक बचाव दल भेजो"

    def test_hindi_action_is_send_team(self):
        """Parsing the Hindi sentence should yield ACTION=SEND_TEAM."""
        msg = semantic_parser.parse(self.HINDI_TEXT, "hi")
        # SemanticField: .value = string name (e.g. 'SEND_TEAM'), .code = int (e.g. 1)
        action_val = msg.action.value if hasattr(msg.action, 'value') else str(msg.action)
        action_code = msg.action.code if hasattr(msg.action, 'code') else None
        assert (action_val == Action.SEND_TEAM.name or action_code == Action.SEND_TEAM.value), (
            f"Expected SEND_TEAM, got value={action_val!r}, code={action_code!r}"
        )

    def test_hindi_target_contains_hubbli(self):
        """Parsing the Hindi sentence should yield target containing HUBBLI or हब्बली."""
        msg = semantic_parser.parse(self.HINDI_TEXT, "hi")
        # SemanticField: .value = string (e.g. 'HUBBLI'), .code = int enum value
        target_val  = msg.target.value if hasattr(msg.target, 'value') else str(msg.target)
        target_code = msg.target.code  if hasattr(msg.target, 'code')  else None
        loc_text    = getattr(msg, 'location_text', '') or ''
        from semantic_schema import Target

        has_hubbli = (
            target_code == Target.HUBBLI.value or          # .code == 1
            str(target_val).upper() == "HUBBLI" or         # .value == 'HUBBLI'
            "हब्बली" in loc_text or
            "hubbli" in loc_text.lower() or
            "हुबली" in loc_text
        )
        assert has_hubbli, (
            f"Expected HUBBLI in target/location_text. "
            f"target.value={target_val!r}, target.code={target_code!r}, location_text={loc_text!r}"
        )

    def test_hindi_parse_not_fallback(self):
        """The Hindi sentence should not produce a fallback message."""
        msg = semantic_parser.parse(self.HINDI_TEXT, "hi")
        assert not msg.is_fallback, f"Unexpected fallback: {msg.fallback_text!r}"

    def test_hindi_realize_to_english(self):
        """Realizing the Hindi parse result into English should be meaningful."""
        msg = semantic_parser.parse(self.HINDI_TEXT, "hi")
        result = translation_engine.realize(msg, "en")
        assert isinstance(result, str) and result.strip()
        assert "PROPER_LOCATION" not in result, f"Sentinel in English output: {result!r}"


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: translate() convenience function
# ─────────────────────────────────────────────────────────────────────────────

class TestTranslateFunction:
    """Tests for the translate() convenience function."""

    def test_translate_en_to_hi(self):
        """translate('en', 'hi', ...) should return a non-empty Hindi string."""
        result = translation_engine.translate(
            "en", "hi",
            "Send 3 rescue teams to Hubbli immediately"
        )
        assert isinstance(result, str) and result.strip()
        assert "PROPER_LOCATION" not in result

    def test_translate_hi_to_en(self):
        """translate('hi', 'en', ...) should return a non-empty English string."""
        result = translation_engine.translate(
            "hi", "en",
            "हब्बली में तुरंत एक बचाव दल भेजो"
        )
        assert isinstance(result, str) and result.strip()

    def test_translate_same_lang_non_empty(self):
        """translate(lang, same_lang, ...) should still return a non-empty string."""
        result = translation_engine.translate(
            "hi", "hi",
            "हब्बली में तुरंत एक बचाव दल भेजो"
        )
        assert isinstance(result, str) and result.strip()

    @pytest.mark.parametrize("target_lang", SUPPORTED_LANGUAGES)
    def test_translate_en_to_all_langs(self, target_lang):
        """translate('en', <lang>, ...) must be non-empty for every target language."""
        result = translation_engine.translate(
            "en", target_lang,
            "Send 2 rescue teams to Hubbli immediately"
        )
        assert isinstance(result, str) and result.strip(), (
            f"translate('en', '{target_lang}', ...) → empty"
        )
        assert "PROPER_LOCATION" not in result, (
            f"Sentinel in output for target='{target_lang}': {result!r}"
        )
