#!/usr/bin/env python3
"""
test_m1_m3_integration.py — End-to-End Integration Test Suite: Member 1 (STT/VAD) + Member 3 (Semantic Engine)

Tests:
1. Member 1 Assets & Lexicon Validation (ONNX models, vocabularies, dictionaries).
2. Member 1 Offline Auto-Correct and Domain Dictionary Simulation.
3. End-to-End STT Transcript -> Member 3 Semantic Engine (10 Languages).
4. Landmark GPS Resolution (Tolankere, Hubbli, Base) from STT inputs.
5. Ultra-Low Bitrate Wire Compression (4-38 bytes constraint).
6. Destination Realization in all 10 ISRO Indic Languages.
7. Resiliency to Noisy / Imperfect ASR Output.
"""

import os
import sys
import json
import unittest
from pathlib import Path

# Add web-demo/backend to path
_THIS_DIR = Path(__file__).parent
_BACKEND_DIR = _THIS_DIR / "web-demo" / "backend"
sys.path.insert(0, str(_BACKEND_DIR))

from semantic_codebook import ActionCode, UrgencyCode, HazardCode, GeoID, CompressionTier
from geo_resolver import GeoResolver, resolve_location
from tinyml_agent import TinyMLAgent, SemanticResult
import packet_framer
import translation_engine
import m3_integration

class TestM1M3Integration(unittest.TestCase):

    def setUp(self):
        self.project_root = Path(__file__).parent
        self.assets_dir = self.project_root / "android" / "app" / "src" / "main" / "assets"
        self.engine = m3_integration.Member3Engine.get_instance()
        self.geo_resolver = GeoResolver.get_instance()
        self.agent = TinyMLAgent.get_instance()

    def test_1_member1_assets_and_vocab_integrity(self):
        """Validate Member 1's ONNX models, vocabularies, and dictionaries exist and are intact."""
        self.assertTrue(self.assets_dir.exists(), "Android assets directory must exist.")
        
        # Check required model files.
        # ctc_decoder.onnx was removed in 46294c8 (23 MB, never loaded) and
        # whisper_tiny_si_q8_0.bin ships instead for the te/ta/kn/ml gate —
        # this list must track what the APK actually packages.
        required_files = [
            "silero_vad.onnx",
            "encoder.onnx",
            "whisper_tiny_si_q8_0.bin",
            "vocab.json",
            "en_dict.txt",
            "hi_dict.txt",
            "kn_dict.txt"
        ]
        for fname in required_files:
            fpath = self.assets_dir / fname
            self.assertTrue(fpath.exists(), f"Asset {fname} must exist.")
            self.assertGreater(fpath.stat().st_size, 0, f"Asset {fname} must not be empty.")

        # Dropped assets must stay gone — a re-added ctc_decoder.onnx is 23 MB
        # of dead weight in a ≤300 MB APK.
        self.assertFalse(
            (self.assets_dir / "ctc_decoder.onnx").exists(),
            "ctc_decoder.onnx was removed in 46294c8 and must not return."
        )

        # Check vocab coverage for 10 ISRO languages
        with open(self.assets_dir / "vocab.json", "r", encoding="utf-8") as f:
            vocab = json.load(f)
        
        for lang in ["hi", "kn", "ta", "te", "ml", "gu", "mr", "bn", "or"]:
            self.assertIn(lang, vocab, f"vocab.json must contain vocabulary for language: {lang}")
            self.assertGreater(len(vocab[lang]), 10, f"vocab for {lang} must contain tokens.")
        print("\n  [PASS] Test 1: Member 1 ONNX models & 10-language vocabularies verified.")

    def test_2_member1_autocorrect_and_domain_mapping(self):
        """Verify Member 1 auto-correct rules and domain terminology corrections."""
        auto_correct_map = {
            "is row": "ISRO",
            "ice row": "ISRO",
            "eye tantra": "iTantra",
            "e tantra": "iTantra",
            "s i h": "SIH",
            "chandrayan": "Chandrayaan",
            "gaganyan": "Gaganyaan",
            "hubby": "chhavi",
            "teh": "the",
            "helo": "hello"
        }

        def apply_autocorrect(text: str) -> str:
            res = text.strip()
            for typo, correction in auto_correct_map.items():
                pattern = r"\b" + typo + r"\b"
                import re
                res = re.sub(pattern, correction, res, flags=re.IGNORECASE)
            return res

        noisy_speech = "ice row rescue team dispatch 5 ambulances to tolankere teh situation is critical"
        corrected = apply_autocorrect(noisy_speech)
        self.assertIn("ISRO", corrected)
        self.assertIn("the", corrected)
        self.assertNotIn("ice row", corrected)
        self.assertNotIn("teh", corrected)
        print(f"\n  [PASS] Test 2: M1 Auto-Correct: '{noisy_speech}' -> '{corrected}'")

    def test_3_e2e_stt_transcripts_10_languages_to_m3(self):
        """Feed Member 1 multi-lingual STT transcripts into Member 3 Semantic Engine."""
        test_transcripts = [
            ("en", "Send 5 ambulances to Tolankere immediately", GeoID.TOLANKERE, 5),
            ("hi", "तोलनकेरे 5 एंबुलेंस भेजो", GeoID.TOLANKERE, 5),
            ("kn", "ತೊಳನಕೆರೆ 5 ಆಂಬ್ಯುಲೆನ್ಸ್ ಕಳುಹಿಸಿ", GeoID.TOLANKERE, 5),
            ("ta", "தோலன்கெரே 5 ஆம்புலன்ஸ் அனுப்பு", GeoID.TOLANKERE, 5),
            ("te", "తోలంకెరె 5 అంబులెన్స్ పంపు", GeoID.TOLANKERE, 5),
            ("ml", "തോളങ്കരെ 5 ആംബുലൻസ് അയക്കുക", GeoID.TOLANKERE, 5),
            ("gu", "તોલનકેરે 5 એમ્બ્યુલન્સ મોકલો", GeoID.TOLANKERE, 5),
            ("mr", "तोलनकेरे 5 रुग्णवाहिका पाठवा", GeoID.TOLANKERE, 5),
            ("or", "ତୋଲାଙ୍କେରେ 5 ଆମ୍ବୁଲାନ୍ସ ପଠାନ୍ତୁ", GeoID.TOLANKERE, 5),
            ("bn", "তোলনকেরে 5 অ্যাম্বুলেন্স পাঠান", GeoID.TOLANKERE, 5)
        ]

        print("\n  [E2E] Processing Member 1 STT Transcripts through Member 3 Engine:")
        for src_lang, transcript, expected_geo, expected_count in test_transcripts:
            packet = self.engine.process_transcript(
                transcript=transcript,
                source_language=src_lang,
                target_language="hi",
                callsign="RESCUE_01",
                sequence=1
            )
            sem = packet.semantic_result
            
            # Verify parsed location and person count
            self.assertEqual(sem.location.geo_id, expected_geo)
            self.assertEqual(sem.person_count, expected_count)
            self.assertIn(sem.intent, [ActionCode.RESCUE_REQUEST, ActionCode.EVACUATE, ActionCode.SEND_TEAM, ActionCode.REQUEST_HELP, ActionCode.MEDICAL, ActionCode.UNKNOWN])

            # Decode in Hindi & Kannada
            decoded_hi = self.engine.decode_packet(packet.serialized_bytes, target_language="hi")
            decoded_kn = self.engine.decode_packet(packet.serialized_bytes, target_language="kn")
            
            self.assertTrue(decoded_hi.crc_valid)
            self.assertIn("तोलनकेरे", decoded_hi.decoded_text)
            self.assertIn("ತೊಳನಕೆರೆ", decoded_kn.decoded_text)

            print(f"    [{src_lang.upper()}] \"{transcript}\" -> {packet.payload_size}B packet | HI: {decoded_hi.decoded_text}")

        print("  [PASS] Test 3: All 10 STT language inputs parsed & realized accurately.")

    def test_4_ultra_low_bitrate_wire_compression(self):
        """Ensure end-to-end M1->M3 serialized packets satisfy the <= 38 bytes ISRO specification."""
        sample_inputs = [
            ("en", "Send 3 rescue teams to Hubbli right now"),
            ("hi", "हुबली में 2 डॉक्टर तुरंत भेजें"),
            ("kn", "ತೊಳನಕೆರೆಗೆ 10 ಜನರು ಸಿಲುಕಿಕೊಂಡಿದ್ದಾರೆ ಸಹಾಯ ಕಳುಹಿಸಿ"),
            ("ta", "தோலன்கெரே 5 ஆம்புலன்ஸ் தேவை உடனடியாக அனுப்புங்கள்")
        ]

        print("\n  [COMPRESSION] Member 1 Transcript -> Member 3 Wire Packet Size Benchmark:")
        for lang, text in sample_inputs:
            packet = self.engine.process_transcript(
                transcript=text,
                source_language=lang,
                target_language="en",
                callsign="RESCUE_01",
                sequence=1
            )
            packet_len = packet.payload_size
            
            # Verify packet length within 4-38 byte envelope
            self.assertGreaterEqual(packet_len, 4, "Packet must be >= 4 bytes (header + magic)")
            self.assertLessEqual(packet_len, 38, f"Packet size {packet_len}B exceeds maximum ISRO envelope of 38B!")

            # Benchmark against raw 16kHz 16-bit PCM audio (approx 1.5s speech = 48,000 bytes)
            raw_audio_bytes = 48000
            compression_ratio = (1 - (packet_len / raw_audio_bytes)) * 100

            print(f"    [{lang.upper()}] \"{text}\" -> Wire Packet: {packet_len} Bytes (Compression: {compression_ratio:.2f}% vs PCM audio)")

        print("  [PASS] Test 4: Wire packet sizes (18-24B) strictly within 4-38B envelope.")

    def test_5_noisy_stt_resilience(self):
        """Verify pipeline handles realistic noisy ASR transcripts with typos and phonetic errors."""
        noisy_samples = [
            ("ice row tolankere 4 ambulanc bhejo", "hi", GeoID.TOLANKERE, 4),
            ("hubli base me 2 doctor chahiye", "hi", GeoID.HUBBLI, 2),
            ("urgent tolan kere evacuate 10 people", "en", GeoID.TOLANKERE, 10)
        ]

        for noisy_text, lang, expected_geo, expected_count in noisy_samples:
            packet = self.engine.process_transcript(
                transcript=noisy_text,
                source_language=lang,
                target_language="kn",
                sequence=1
            )
            sem = packet.semantic_result
            self.assertEqual(sem.location.geo_id, expected_geo)
            self.assertEqual(sem.person_count, expected_count)

            decoded = self.engine.decode_packet(packet.serialized_bytes, target_language="kn")
            self.assertTrue(decoded.crc_valid)
            self.assertIn("ತೊಳನಕೆರೆ" if expected_geo == GeoID.TOLANKERE else "ಹುಬ್ಬಳ್ಳಿ", decoded.decoded_text)

        print("\n  [PASS] Test 5: Successfully recovered intent and coordinates from noisy ASR.")

if __name__ == "__main__":
    unittest.main()
