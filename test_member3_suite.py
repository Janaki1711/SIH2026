#!/usr/bin/env python3
"""
test_member3_suite.py — Comprehensive Test Suite for iTantra Member 3 Module

Covers all 7 mandatory test cases specified by SIH 2026:
  Test 1: Simple emergency ("Help, there is a flood.") -> Tier 1 Macro (6-8B)
  Test 2: Structured emergency ("Five people are trapped near Tolankere because of flooding.") -> Tier 2 (18-22B)
  Test 3: Unknown arbitrary sentence -> Tier 3 Fallback (35-38B) without silent loss
  Test 4: Multilingual input (Hindi, Kannada, Tamil, Marathi, English)
  Test 5: Encode/decode round trip (semantic preservation & 16-byte prosody vector)
  Test 6: CRC16 corruption rejection (1-bit flip fails validation)
  Test 7: Payload-size boundary validation (Tier 1: 6-8B, Tier 2: 18-22B, Tier 3: 35-38B)
"""

import sys
import os
import unittest

# Add backend directory to sys.path
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.join(_THIS_DIR, "web-demo", "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from semantic_codebook import ActionCode, UrgencyCode, HazardCode, GeoID, CompressionTier
from geo_resolver import GeoResolver, resolve_location
from tinyml_agent import TinyMLAgent, SemanticResult
import semantic_compressor
import packet_framer
import translation_engine
import m3_integration


class TestMember3Suite(unittest.TestCase):

    def setUp(self):
        self.engine = m3_integration.Member3Engine.get_instance()
        self.geo_resolver = GeoResolver.get_instance()

    def test_1_simple_emergency(self):
        """Test 1: Simple emergency -> valid semantic result, Tier 1, valid Protobuf & CRC."""
        text = "Help, there is a flood."
        packet = self.engine.process_transcript(
            transcript=text,
            source_language="en",
            target_language="en",
            callsign="RESCUE_01",
            sequence=101
        )

        # 1. Verify semantic extraction
        sem = packet.semantic_result
        self.assertEqual(sem.intent, ActionCode.RESCUE_REQUEST)
        self.assertEqual(sem.hazard, HazardCode.FLOOD)
        self.assertEqual(sem.urgency, UrgencyCode.CRITICAL_SOS)

        # 2. Verify compression tier & payload size
        self.assertEqual(packet.compression_tier, CompressionTier.TIER_1_MACRO)
        self.assertGreaterEqual(packet.payload_size, 6)
        self.assertLessEqual(packet.payload_size, 8)

        # 3. Verify Protobuf framing & CRC validation
        self.assertTrue(packet_framer.validate_frame(packet.serialized_bytes))
        decoded = self.engine.decode_packet(packet.serialized_bytes, target_language="en")
        self.assertTrue(decoded.crc_valid)
        self.assertEqual(decoded.intent, ActionCode.RESCUE_REQUEST)
        self.assertEqual(decoded.hazard, HazardCode.FLOOD)

    def test_2_structured_emergency(self):
        """Test 2: Structured emergency -> Tolankere (0x4F2A), count=5, hazard=FLOOD, Tier 2."""
        text = "Five people are trapped near Tolankere because of flooding."
        packet = self.engine.process_transcript(
            transcript=text,
            source_language="en",
            target_language="hi",
            callsign="COMMAND_01",
            sequence=102
        )

        sem = packet.semantic_result
        self.assertEqual(sem.intent, ActionCode.RESCUE_REQUEST)
        self.assertEqual(sem.person_count, 5)
        self.assertEqual(sem.hazard, HazardCode.FLOOD)
        self.assertEqual(sem.location.geo_id, GeoID.TOLANKERE)
        self.assertEqual(sem.location.canonical_name, "Tolankere")
        self.assertEqual(sem.urgency, UrgencyCode.CRITICAL_SOS)

        # Verify Tier 2 payload boundary
        self.assertEqual(packet.compression_tier, CompressionTier.TIER_2_STRUCTURED)
        self.assertGreaterEqual(packet.payload_size, 18)
        self.assertLessEqual(packet.payload_size, 22)

        # Verify round-trip decode in Hindi
        decoded = self.engine.decode_packet(packet.serialized_bytes, target_language="hi")
        self.assertTrue(decoded.crc_valid)
        self.assertEqual(decoded.person_count, 5)
        self.assertEqual(decoded.location.geo_id, GeoID.TOLANKERE)
        self.assertIn("तोलनकेरे", decoded.decoded_text)
        self.assertIn("5", decoded.decoded_text)

    def test_3_unknown_sentence_fallback(self):
        """Test 3: Unknown arbitrary sentence -> Clean Tier 3 fallback, no false macro, no silent loss."""
        text = "The weather forecast indicates mild clouds over the valley tomorrow morning."
        packet = self.engine.process_transcript(
            transcript=text,
            source_language="en",
            target_language="en",
            sequence=103
        )

        sem = packet.semantic_result
        self.assertTrue(sem.is_fallback)
        self.assertEqual(packet.compression_tier, CompressionTier.TIER_3_FALLBACK)
        self.assertGreaterEqual(packet.payload_size, 35)
        self.assertLessEqual(packet.payload_size, 38)

        # Verify decoded message recovers text safely
        decoded = self.engine.decode_packet(packet.serialized_bytes, target_language="en")
        self.assertTrue(decoded.crc_valid)
        self.assertIn("weather forecast", decoded.decoded_text)

    def test_4_multilingual_input(self):
        """Test 4: Multilingual inputs (Hindi, Kannada, Tamil, Marathi, English)."""
        test_cases = [
            ("hi", "तोलनकेरे के पास पांच लोग फंसे हुए हैं, तुरंत नाव भेजो", GeoID.TOLANKERE, ActionCode.RESCUE_REQUEST, 5),
            ("kn", "ತೊಳನಕೆರೆ ಹತ್ತಿರ ಜನರು ಸಿಲುಕಿಕೊಂಡಿದ್ದಾರೆ, ಸಹಾಯ ಕಳುಹಿಸಿ", GeoID.TOLANKERE, ActionCode.RESCUE_REQUEST, 0),
            ("ta", "தோலன்கெரே அருகில் வெள்ளம் வந்துள்ளது, உதவி தேவை", GeoID.TOLANKERE, ActionCode.RESCUE_REQUEST, 0),
            ("mr", "तोलनकेरे जवळ पूर आला आहे, तातडीने मदत पाठवा", GeoID.TOLANKERE, ActionCode.RESCUE_REQUEST, 0),
            ("en", "Five people are trapped near Tolankere because of flooding.", GeoID.TOLANKERE, ActionCode.RESCUE_REQUEST, 5),
            ("gu", "તોલનકેરે નજીક પાંચ લોકો ફસાયા છે, તાત્કાલિક મદદ મોકલો", GeoID.TOLANKERE, ActionCode.RESCUE_REQUEST, 5),
            ("ml", "തോളങ്കരെ സമീപം ആളുകൾ കുടുങ്ങിയിരിക്കുന്നു, ഉടൻ സഹായം അയക്കുക", GeoID.TOLANKERE, ActionCode.RESCUE_REQUEST, 0),
            ("te", "తోలంకెరె వద్ద వరదలు వచ్చాయి, సహాయం పంపండి", GeoID.TOLANKERE, ActionCode.RESCUE_REQUEST, 0),
            ("or", "ତୋଲାଙ୍କେରେ ନିକଟରେ ଲୋକ ଫସି ରହିଛନ୍ତି, ତୁରନ୍ତ ସାହାଯ୍ୟ ପଠାଅ", GeoID.TOLANKERE, ActionCode.RESCUE_REQUEST, 0),
            ("bn", "তোলনকেরে এর কাছে মানুষ আটকে আছে, অবিলম্বে সাহায্য পাঠান", GeoID.TOLANKERE, ActionCode.RESCUE_REQUEST, 0),
        ]

        for lang, text, expected_geoid, expected_intent, expected_count in test_cases:
            with self.subTest(lang=lang, text=text):
                packet = self.engine.process_transcript(
                    transcript=text,
                    source_language=lang,
                    target_language=lang
                )
                sem = packet.semantic_result
                self.assertEqual(sem.location.geo_id, expected_geoid, f"Failed GeoID for {lang}")
                self.assertEqual(sem.intent, expected_intent, f"Failed Intent for {lang}")
                if expected_count > 0:
                    self.assertEqual(sem.person_count, expected_count, f"Failed PersonCount for {lang}")
                self.assertTrue(packet_framer.validate_frame(packet.serialized_bytes))

    def test_5_encode_decode_roundtrip_with_prosody(self):
        """Test 5: Round trip with 16-byte prosody vector preservation."""
        dummy_prosody = bytes([0xAA, 0xBB, 0xCC, 0xDD, 0x11, 0x22, 0x33, 0x44,
                              0x55, 0x66, 0x77, 0x88, 0x99, 0xEE, 0xFF, 0x00])
        text = "Five people are trapped near Tolankere because of flooding."
        
        packet = self.engine.process_transcript(
            transcript=text,
            source_language="en",
            target_language="ta",
            prosody_vector=dummy_prosody,
            callsign="RESCUE_HQ",
            sequence=205,
            priority=2
        )

        decoded = self.engine.decode_packet(packet.serialized_bytes, target_language="ta")
        self.assertTrue(decoded.crc_valid)
        self.assertEqual(decoded.person_count, 5)
        self.assertEqual(decoded.location.geo_id, GeoID.TOLANKERE)
        self.assertEqual(decoded.hazard, HazardCode.FLOOD)
        self.assertEqual(decoded.priority, 2)
        self.assertEqual(decoded.prosody_vector, dummy_prosody, "Prosody vector was corrupted or lost in roundtrip!")

    def test_6_crc_corruption_rejection(self):
        """Test 6: CRC corruption rejection — flipping one bit must cause frame rejection."""
        text = "Help, there is a flood."
        packet = self.engine.process_transcript(transcript=text)
        wire_bytes = bytearray(packet.serialized_bytes)

        # Flip one bit in the payload
        corrupt_index = len(wire_bytes) // 2
        wire_bytes[corrupt_index] ^= 0x01

        # Must fail frame validation
        self.assertFalse(packet_framer.validate_frame(bytes(wire_bytes)))
        with self.assertRaises(ValueError):
            self.engine.decode_packet(bytes(wire_bytes))

    def test_7_payload_size_boundaries(self):
        """Test 7: Payload size boundary enforcement."""
        # Tier 1
        t1_res = SemanticResult(
            original_text="Flood alert",
            intent=ActionCode.RESCUE_REQUEST,
            hazard=HazardCode.FLOOD,
            urgency=UrgencyCode.CRITICAL_SOS,
            compression_tier=CompressionTier.TIER_1_MACRO
        )
        t1_bytes = semantic_compressor.compress(t1_res)
        self.assertGreaterEqual(len(t1_bytes), 6)
        self.assertLessEqual(len(t1_bytes), 8)

        # Tier 2
        t2_res = SemanticResult(
            original_text="Five people trapped near Tolankere",
            intent=ActionCode.RESCUE_REQUEST,
            hazard=HazardCode.FLOOD,
            person_count=5,
            location=self.geo_resolver.resolve_location("Tolankere"),
            urgency=UrgencyCode.CRITICAL_SOS,
            compression_tier=CompressionTier.TIER_2_STRUCTURED
        )
        t2_bytes = semantic_compressor.compress(t2_res)
        self.assertGreaterEqual(len(t2_bytes), 18)
        self.assertLessEqual(len(t2_bytes), 22)

        # Tier 3
        t3_res = SemanticResult(
            original_text="Arbitrary fallback text that is unparsed",
            is_fallback=True,
            compression_tier=CompressionTier.TIER_3_FALLBACK
        )
        t3_bytes = semantic_compressor.compress(t3_res)
        self.assertGreaterEqual(len(t3_bytes), 35)
        self.assertLessEqual(len(t3_bytes), 38)

    def test_geo_phonetic_matching(self):
        """Verify phonetic matching for spelling variations."""
        test_variations = [
            ("Tolan care", GeoID.TOLANKERE, "Tolankere"),
            ("Tholankere", GeoID.TOLANKERE, "Tolankere"),
            ("tolankere", GeoID.TOLANKERE, "Tolankere"),
            ("hubly", GeoID.HUBBLI, "Hubbli"),
            ("hubli", GeoID.HUBBLI, "Hubbli"),
            ("Hubballi", GeoID.HUBBLI, "Hubbli"),
        ]
        for query, expected_id, expected_canonical in test_variations:
            with self.subTest(query=query):
                loc = resolve_location(query)
                self.assertEqual(loc.geo_id, expected_id)
                self.assertEqual(loc.canonical_name, expected_canonical)


if __name__ == "__main__":
    unittest.main()
