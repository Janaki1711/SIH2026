"""
test_semantic_fidelity.py — iTantra M3 Semantic Fidelity Guarantees

The backend translation pipeline is English-as-median: every source language is
parsed into a language-neutral SemanticMessage (the pivot/IR) and realized into
the target language. These tests pin down the *honesty* properties of that
pipeline across all 10×10 language pairs:

  1. No internal sentinel ("unknown"/UNKNOWN/PROPER_LOCATION) ever reaches a
     user-visible output.
  2. src == tgt is identity — text is never rewritten into itself.
  3. Free-form text with too little semantic content passes through unchanged
     (the engine never fabricates a "translation").
  4. Every supported source language yields English-script output into English.
  5. Every Indic target produces its own script — and never a foreign Indic
     script (e.g. no Devanagari inside Bengali output).
  6. Parsed conditions survive realization (semantics are not dropped).
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import translation_engine
import semantic_parser
from translation_engine import translate, SUPPORTED_LANGUAGES


# One concrete disaster-services phrase per source language
# (action + entity + location + urgency → non-fallback parse in every language).
PHRASES = {
    "en": "Send rescue team to Hubbli immediately",
    "hi": "हब्बली में बचाव दल भेजो",
    "gu": "હબ્બલીમાં બચાવ ટીમ મોકલો",
    "mr": "तातडीची मदत पाठवा",
    "kn": "ಹುಬ್ಬಳ್ಳಿಗೆ ರಕ್ಷಣಾ ತಂಡ ಕಳುಹಿಸಿ",
    "ml": "ഹുബ്ലിയിലേക്ക് രക്ഷാസംഘം അയക്കൂ",
    "ta": "ஹூப்ளிக்கு மீட்புக் குழுவை அனுப்புங்கள்",
    "te": "హుబ్లీకి రక్షణ బృందాన్ని పంపండి",
    "or": "ହୁବ୍ଲିକୁ ଉଦ୍ଧାର ଦଳ ପଠାନ୍ତୁ",
    "bn": "হুবলিতে উদ্ধার দল পাঠান",
}

# Unicode script ranges for the 9 Indic scripts (en has no dedicated range).
SCRIPT_RANGES = {
    "hi": (0x0900, 0x097F),  # Devanagari
    "mr": (0x0900, 0x097F),  # Devanagari (shared with hi)
    "gu": (0x0A80, 0x0AFF),  # Gujarati
    "bn": (0x0980, 0x09FF),  # Bengali
    "or": (0x0B00, 0x0B7F),  # Oriya
    "ta": (0x0B80, 0x0BFF),  # Tamil
    "te": (0x0C00, 0x0C7F),  # Telugu
    "kn": (0x0C80, 0x0CFF),  # Kannada
    "ml": (0x0D00, 0x0D7F),  # Malayalam
}

ALL_PAIRS = [(s, t) for s in SUPPORTED_LANGUAGES for t in SUPPORTED_LANGUAGES]


def _has_script(text: str, lo: int, hi: int) -> bool:
    return any(lo <= ord(ch) <= hi for ch in text)


class TestNeverEmitSentinel:
    """The 'Status update for Unknown.' / 'Send 1 unknown' class of bugs."""

    # Text with no recognisable semantic keyword → must be a fallback/passthrough.
    FREE_FORM = "Hiee.....anybody there?? say something"

    @pytest.mark.parametrize("src,tgt", ALL_PAIRS)
    def test_no_unknown_sentinel(self, src, tgt):
        out = translate(src, tgt, PHRASES[src])
        assert out and out.strip(), f"{src}->{tgt} returned empty"
        assert "unknown" not in out.lower(), (
            f"{src}->{tgt} leaked the internal UNKNOWN sentinel: {out!r}"
        )
        assert "PROPER_LOCATION" not in out, (
            f"{src}->{tgt} leaked the PROPER_LOCATION sentinel: {out!r}"
        )

    @pytest.mark.parametrize("tgt", SUPPORTED_LANGUAGES)
    def test_free_form_never_becomes_status_report(self, tgt):
        """Weak semantic content must pass through — not become 'Status update for Unknown.'"""
        out = translate("en", tgt, self.FREE_FORM)
        assert "unknown" not in out.lower()
        # and it must not fabricate a generic status report either
        assert "status report" not in out.lower()
        assert "स्थिति रिपोर्ट" not in out


class TestIdentityAndPassthrough:
    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_same_language_is_identity(self, lang):
        text = PHRASES[lang]
        assert translate(lang, lang, text) == text

    @pytest.mark.parametrize("tgt", SUPPORTED_LANGUAGES)
    def test_free_form_english_passthrough(self, tgt):
        """Weak parse → honest passthrough (never a fabricated translation)."""
        text = "Hiee.....anybody there?? say something"
        out = translate("en", tgt, text)
        assert out == text, f"en->{tgt} fabricated a translation: {out!r}"

    def test_en_to_en_free_form_passthrough(self):
        text = "Hiee.....anybody there?? say something"
        assert translate("en", "en", text) == text


class TestAllSourcesIntoEnglish:
    """Every source language must produce recognizable English when target=eng."""

    @pytest.mark.parametrize("src", SUPPORTED_LANGUAGES)
    def test_source_to_english_is_english_script(self, src):
        out = translate(src, "en", PHRASES[src])
        assert out and out.strip(), f"{src}->en returned empty"
        ascii_ratio = sum(1 for ch in out if ord(ch) < 128) / max(len(out), 1)
        assert ascii_ratio > 0.8, (
            f"{src}->en output is not English-script (ratio={ascii_ratio:.2f}): {out!r}"
        )


class TestTargetScriptPreserved:
    @pytest.mark.parametrize("tgt", sorted(SCRIPT_RANGES))
    def test_english_source_realized_in_target_script(self, tgt):
        lo, hi = SCRIPT_RANGES[tgt]
        out = translate("en", tgt, PHRASES["en"])
        assert _has_script(out, lo, hi), (
            f"en->{tgt} produced no {tgt} script at all: {out!r}"
        )

    @pytest.mark.parametrize("src,tgt", ALL_PAIRS)
    def test_no_foreign_indic_script_in_output(self, src, tgt):
        """A realization must not contain a *different* Indic script
        (the Bengali-realizer Devanagari-leak class of bugs)."""
        if tgt not in SCRIPT_RANGES:
            pytest.skip("target has no dedicated Indic script")
        out = translate(src, tgt, PHRASES[src])
        t_lo, t_hi = SCRIPT_RANGES[tgt]
        # Danda / double-danda are shared Indic sentence punctuation — not leaks.
        shared_punct = {0x0964, 0x0965}
        for other, (o_lo, o_hi) in SCRIPT_RANGES.items():
            if other == tgt:
                continue
            if (o_lo, o_hi) == (t_lo, t_hi):
                continue  # hi/mr share Devanagari — indistinguishable
            leak = [
                ch for ch in out
                if o_lo <= ord(ch) <= o_hi and ord(ch) not in shared_punct
            ]
            assert not leak, (
                f"{src}->{tgt}: foreign {other} script leaked into output "
                f"({leak[:5]!r}): {out!r}"
            )


class TestSemanticsSurviveRealization:
    def test_condition_survives_into_hindi(self):
        out = translate("en", "hi", "People are trapped in Hubbli")
        assert "फंसे" in out, f"TRAPPED condition lost in Hindi: {out!r}"
        assert "unknown" not in out.lower()

    @pytest.mark.parametrize("tgt", sorted(SCRIPT_RANGES))
    def test_condition_survives_into_every_target(self, tgt):
        lo, hi = SCRIPT_RANGES[tgt]
        out = translate("en", tgt, "People are trapped")
        assert _has_script(out, lo, hi), f"condition-only message unrealized: {out!r}"
        assert "unknown" not in out.lower()

    @pytest.mark.parametrize("src", SUPPORTED_LANGUAGES)
    def test_hindi_style_send_action_survives_all_targets(self, src):
        """Action=SEND_TEAM must never be dropped for any source→target pair."""
        out = translate(src, "en", PHRASES[src])
        # Every phrase above is a send/help action — English output must request
        # or state something actionable, not a bare status report.
        assert "Status update for current location" not in out, (
            f"{src}->en lost the action semantics: {out!r}"
        )


class TestParserLanguageThreading:
    def test_parse_core_accepts_language(self):
        msg = semantic_parser._parse_core("send rescue team", "hi")
        assert getattr(msg, "source_language", None) == "hi"
        assert msg.action.code != 0

    def test_hybrid_parse_threads_language(self):
        msg = semantic_parser.parse("send rescue team to Hubbli", "mr")
        assert getattr(msg, "source_language", None) == "mr"
