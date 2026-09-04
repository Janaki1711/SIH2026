"""
tinyml_agent.py — Multi-Task TinyML Semantic Agent

Extracts intent, action, hazard, location entities (using GeoResolver),
person count, and vocal urgency triage. Produces a complete SemanticResult.
"""

import re
from typing import Dict, Any, List, Optional
from semantic_codebook import ActionCode, UrgencyCode, HazardCode, GeoID, CompressionTier
from geo_resolver import GeoResolver, LocationEntity

class SemanticResult:
    def __init__(
        self,
        original_text: str,
        detected_language: str = "en",
        intent: ActionCode = ActionCode.UNKNOWN,
        action: ActionCode = ActionCode.UNKNOWN,
        hazard: HazardCode = HazardCode.NONE,
        location: Optional[LocationEntity] = None,
        person_count: int = 0,
        urgency: UrgencyCode = UrgencyCode.ROUTINE,
        confidence: float = 1.0,
        compression_tier: CompressionTier = CompressionTier.TIER_1_MACRO,
        extracted_entities: Optional[List[Dict[str, Any]]] = None,
        is_fallback: bool = False,
        fallback_reason: str = "",
        prosody_vector: Optional[bytes] = None,
        model_backend_used: str = "DETERMINISTIC_LOCAL_FALLBACK"
    ):
        self.original_text = original_text
        self.detected_language = detected_language
        self.intent = intent
        self.action = action
        self.hazard = hazard
        self.location = location or LocationEntity("", GeoID.UNKNOWN, 0.0)
        self.person_count = person_count
        self.urgency = urgency
        self.confidence = confidence
        self.compression_tier = compression_tier
        self.extracted_entities = extracted_entities or []
        self.is_fallback = is_fallback
        self.fallback_reason = fallback_reason
        self.prosody_vector = prosody_vector or bytes(16)
        self.model_backend_used = model_backend_used

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_text": self.original_text,
            "detected_language": self.detected_language,
            "intent": self.intent.name,
            "action": self.action.name,
            "hazard": self.hazard.name,
            "location": self.location.to_dict(),
            "person_count": self.person_count,
            "urgency": self.urgency.name,
            "confidence": round(self.confidence, 3),
            "compression_tier": int(self.compression_tier.value),
            "tier_name": self.compression_tier.name,
            "extracted_entities": self.extracted_entities,
            "is_fallback": self.is_fallback,
            "fallback_reason": self.fallback_reason,
            "has_prosody": len(self.prosody_vector) == 16,
            "model_backend_used": self.model_backend_used,
        }


class TinyMLAgent:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.geo_resolver = GeoResolver.get_instance()
        self.ml_model = None  # Placeholder for real INT8 model backend if available

    def analyze(self, text: str, source_language: str = "en", optional_prosody: Optional[bytes] = None) -> SemanticResult:
        if self.ml_model and hasattr(self.ml_model, "is_loaded") and self.ml_model.is_loaded():
            res = self.ml_model.predict(text, source_language)
            if res:
                if optional_prosody:
                    res.prosody_vector = optional_prosody[:16].ljust(16, b'\x00')
                return res

        return self._run_deterministic_fallback(text, source_language, optional_prosody)

    def _run_deterministic_fallback(self, text: str, source_language: str, prosody: Optional[bytes]) -> SemanticResult:
        res = SemanticResult(
            original_text=text,
            detected_language=self._detect_language(text, source_language),
            model_backend_used="DETERMINISTIC_LOCAL_FALLBACK"
        )

        if prosody:
            res.prosody_vector = prosody[:16].ljust(16, b'\x00') if len(prosody) < 16 else prosody[:16]

        # 1. Location Entity Resolution
        res.location = self.geo_resolver.resolve_location(text)
        if res.location.geo_id != GeoID.UNKNOWN:
            res.extracted_entities.append({"key": "LOCATION", "value": res.location.canonical_name, "confidence": res.location.confidence})

        # 2. Intent & Action Extraction
        res.intent, res.action = self._extract_action_and_intent(text)
        if res.intent != ActionCode.UNKNOWN:
            res.extracted_entities.append({"key": "INTENT", "value": res.intent.name, "confidence": 0.92})

        # 3. Hazard Extraction
        res.hazard = self._extract_hazard(text)
        if res.hazard != HazardCode.NONE:
            res.extracted_entities.append({"key": "HAZARD", "value": res.hazard.name, "confidence": 0.95})

        # 4. Person Count Extraction
        res.person_count = self._extract_person_count(text)
        if res.person_count > 0:
            res.extracted_entities.append({"key": "PERSON_COUNT", "value": str(res.person_count), "confidence": 0.98})

        # 5. Urgency Classification
        res.urgency = self._classify_urgency(text, res.intent, res.hazard, res.prosody_vector)

        # 6. Tier Selection
        if res.intent == ActionCode.UNKNOWN and res.hazard == HazardCode.NONE and res.location.geo_id == GeoID.UNKNOWN:
            res.is_fallback = True
            res.fallback_reason = "Unrecognized semantic intent / out-of-codebook natural language"
            res.confidence = 0.35
            res.compression_tier = CompressionTier.TIER_3_FALLBACK
        elif res.location.geo_id != GeoID.UNKNOWN or res.person_count > 0 or len(res.extracted_entities) >= 3:
            res.is_fallback = False
            res.confidence = 0.90
            res.compression_tier = CompressionTier.TIER_2_STRUCTURED
        else:
            res.is_fallback = False
            res.confidence = 0.95
            res.compression_tier = CompressionTier.TIER_1_MACRO

        return res

    def _detect_language(self, text: str, fallback_lang: str) -> str:
        if fallback_lang and fallback_lang != "auto":
            return fallback_lang
        for ch in text:
            code = ord(ch)
            if 0x0900 <= code <= 0x097F:
                return "hi"
            if 0x0B80 <= code <= 0x0BFF:
                return "ta"
            if 0x0C00 <= code <= 0x0C7F:
                return "te"
            if 0x0C80 <= code <= 0x0CFF:
                return "kn"
        return "en"

    def _extract_person_count(self, text: str) -> int:
        num_words = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "एक": 1, "दो": 2, "दोन": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "पाच": 5,
            "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
            "ஒன்று": 1, "இரண்டு": 2, "மூன்று": 3, "நான்கு": 4, "ஐந்து": 5,
            "ఒకటి": 1, "రెండు": 2, "మూడు": 3, "నాలుగు": 4, "ఐదు": 5,
            "ಒಂದು": 1, "ಎರಡು": 2, "ಮೂರು": 3, "ನಾಲ್ಕು": 4, "ಐದು": 5
        }
        for w, c in num_words.items():
            if w in text.lower():
                return c
        m = re.search(r'\b(\d+)\s*(people|persons|trapped|victims|casualties|men|women|children|लोग|व्यक्तियों)?\b', text, re.I)
        if m:
            return int(m.group(1))
        return 0

    def _extract_hazard(self, text: str) -> HazardCode:
        tl = text.lower()
        if any(w in tl for w in ["flood", "flooding", "बाढ़", "पाणी", "வெள்ளம்", "వరదలు", "ಪ್ರವಾಹ"]):
            return HazardCode.FLOOD
        if any(w in tl for w in ["fire", "blaze", "आग", "தீ", "ಬೆಂಕಿ"]):
            return HazardCode.FIRE
        if any(w in tl for w in ["earthquake", "भूकंप"]):
            return HazardCode.EARTHQUAKE
        if any(w in tl for w in ["landslide", "भूस्खलन"]):
            return HazardCode.LANDSLIDE
        if any(w in tl for w in ["collapse", "collapsed", "गिर गया"]):
            return HazardCode.BUILDING_COLLAPSE
        if any(w in tl for w in ["explosion", "blast", "धमाका", "विस्फोट"]):
            return HazardCode.EXPLOSION
        if any(w in tl for w in ["gas leak", "toxic"]):
            return HazardCode.GAS_LEAK
        return HazardCode.NONE

    def _extract_action_and_intent(self, text: str) -> tuple[ActionCode, ActionCode]:
        tl = text.lower()
        if any(w in tl for w in ["rescue", "help", "trapped", "stuck", "मदद", "मदत", "बचाओ", "वाचवा", "फंसे", "உதவி", "காப்பாற்று", "సహాయం", "ಸಹಾಯ", "ರಕ್ಷಿಸಿ", "send help"]):
            if any(w in tl for w in ["boat", "नाव", "படகு"]):
                return ActionCode.RESCUE_REQUEST, ActionCode.BOAT
            if any(w in tl for w in ["team", "दल", "भेजो", "पाठवा", "send", "ಅನುಪ್ಪು", "ಕಳುಹಿಸಿ"]):
                return ActionCode.RESCUE_REQUEST, ActionCode.SEND_TEAM
            return ActionCode.RESCUE_REQUEST, ActionCode.RESCUE_REQUEST

        if any(w in tl for w in ["evacuate", "evacuation", "खाली करो", "निकालो"]):
            return ActionCode.EVACUATE, ActionCode.EVACUATE
        if any(w in tl for w in ["medical", "doctor", "ambulance", "injured", "चिकित्सा", "घायल"]):
            return ActionCode.MEDICAL, ActionCode.MEDICAL
        if any(w in tl for w in ["supplies", "food", "water", "ration", "राशन", "पानी"]):
            return ActionCode.SUPPLIES, ActionCode.SUPPLIES
        if any(w in tl for w in ["search", "missing", "खोजो", "गायब"]):
            return ActionCode.SEARCH, ActionCode.SEARCH
        if any(w in tl for w in ["alert", "warning", "चेतावनी"]):
            return ActionCode.ALERT, ActionCode.ALERT
        if any(w in tl for w in ["moving", "advance", "आगे बढ़"]):
            return ActionCode.MOVE, ActionCode.MOVE
        if any(w in tl for w in ["report", "status", "सूचना"]):
            return ActionCode.REPORT, ActionCode.REPORT
        return ActionCode.UNKNOWN, ActionCode.UNKNOWN

    def _classify_urgency(self, text: str, intent: ActionCode, hazard: HazardCode, acoustic_prosody: bytes) -> UrgencyCode:
        if acoustic_prosody and len(acoustic_prosody) >= 16:
            if acoustic_prosody[0] >= 0xD0:
                return UrgencyCode.CRITICAL_SOS
            elif acoustic_prosody[0] >= 0x80:
                return UrgencyCode.TACTICAL

        tl = text.lower()
        if (any(w in tl for w in ["immediately", "immediate", "urgent", "sos", "critical", "right now", "asap", "emergency", "तुरंत", "फौरन", "आपातकाल", "உடனடியாக", "వెంటనే", "ತಕ್ಷಣ"])
            or intent in (ActionCode.RESCUE_REQUEST, ActionCode.SOS)
            or hazard in (HazardCode.FLOOD, HazardCode.FIRE, HazardCode.EXPLOSION)):
            return UrgencyCode.CRITICAL_SOS

        if any(w in tl for w in ["quickly", "fast", "soon", "जल्दी"]) or intent in (ActionCode.EVACUATE, ActionCode.MOVE, ActionCode.SEARCH):
            return UrgencyCode.TACTICAL

        return UrgencyCode.ROUTINE


def analyze_transcript(text: str, source_language: str = "en", optional_prosody: Optional[bytes] = None) -> SemanticResult:
    return TinyMLAgent.get_instance().analyze(text, source_language, optional_prosody)
