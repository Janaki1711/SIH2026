"""
m3_integration.py — Public Integration Interface for Member 3

Exposes:
- process_transcript(transcript, source_lang, target_lang, prosody_vector, callsign, sequence, priority)
- decode_packet(wire_bytes, target_lang)
- Telemetry calculation
"""

import time
from typing import Optional, Dict, Any
from semantic_codebook import CompressionTier, UrgencyCode, PriorityLevel
from tinyml_agent import TinyMLAgent, SemanticResult
import semantic_compressor
import packet_framer
import translation_engine

class EncodedSemanticPacket:
    def __init__(
        self,
        serialized_bytes: bytes,
        compression_tier: CompressionTier,
        payload_size: int,
        semantic_result: SemanticResult,
        priority: int,
        source_language: str,
        target_language: str,
        sequence_number: int,
        telemetry: Dict[str, Any]
    ):
        self.serialized_bytes = serialized_bytes
        self.compression_tier = compression_tier
        self.payload_size = payload_size
        self.semantic_result = semantic_result
        self.priority = priority
        self.source_language = source_language
        self.target_language = target_language
        self.sequence_number = sequence_number
        self.telemetry = telemetry

    def to_dict(self) -> Dict[str, Any]:
        return {
            "serialized_bytes_hex": self.serialized_bytes.hex(),
            "serialized_bytes_len": len(self.serialized_bytes),
            "compression_tier": int(self.compression_tier.value),
            "tier_name": self.compression_tier.name,
            "payload_size": self.payload_size,
            "semantic_result": self.semantic_result.to_dict(),
            "priority": self.priority,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "sequence_number": self.sequence_number,
            "telemetry": self.telemetry,
        }


class DecodedSemanticMessage:
    def __init__(
        self,
        decoded_text: str,
        source_language: str,
        target_language: str,
        priority: int,
        urgency: UrgencyCode,
        semantic_result: SemanticResult,
        prosody_vector: bytes,
        crc_valid: bool,
        decode_time_ms: float
    ):
        self.decoded_text = decoded_text
        self.source_language = source_language
        self.target_language = target_language
        self.priority = priority
        self.urgency = urgency
        self.semantic_result = semantic_result
        self.intent = semantic_result.intent
        self.action = semantic_result.action
        self.hazard = semantic_result.hazard
        self.person_count = semantic_result.person_count
        self.location = semantic_result.location
        self.prosody_vector = prosody_vector
        self.crc_valid = crc_valid
        self.decode_time_ms = decode_time_ms


    def to_dict(self) -> Dict[str, Any]:
        return {
            "decoded_text": self.decoded_text,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "priority": self.priority,
            "urgency": self.urgency.name,
            "semantic_result": self.semantic_result.to_dict(),
            "has_prosody": len(self.prosody_vector) == 16,
            "crc_valid": self.crc_valid,
            "decode_time_ms": round(self.decode_time_ms, 3),
        }


class Member3Engine:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.agent = TinyMLAgent.get_instance()

    def process_transcript(
        self,
        transcript: str,
        source_language: str = "en",
        target_language: str = "en",
        prosody_vector: Optional[bytes] = None,
        callsign: str = "CMD_ALPHA",
        sequence: int = 1,
        priority: int = -1
    ) -> EncodedSemanticPacket:
        t_start = time.perf_counter()

        # 1. Semantic Analysis
        t_infer_start = time.perf_counter()
        sem_res = self.agent.analyze(transcript, source_language, prosody_vector)
        t_infer_ms = (time.perf_counter() - t_infer_start) * 1000

        # Determine priority
        if priority < 0:
            if sem_res.urgency == UrgencyCode.CRITICAL_SOS:
                p_level = int(PriorityLevel.LIFE_SAFETY_ALERT)
            elif sem_res.urgency == UrgencyCode.TACTICAL:
                p_level = int(PriorityLevel.TACTICAL)
            else:
                p_level = int(PriorityLevel.ROUTINE)
        else:
            p_level = priority

        # 2. 3-Tier Semantic Compression
        compressed_payload = semantic_compressor.compress(sem_res)
        payload_size = len(compressed_payload)

        # 3. Protobuf Framing with CRC16
        t_frame_start = time.perf_counter()
        wire_bytes = packet_framer.frame_packet(
            compressed_payload=compressed_payload,
            source_language=sem_res.detected_language,
            callsign=callsign,
            sequence=sequence,
            priority=p_level,
            prosody_vector=sem_res.prosody_vector
        )
        t_frame_ms = (time.perf_counter() - t_frame_start) * 1000
        t_total_ms = (time.perf_counter() - t_start) * 1000

        telemetry = {
            "original_text_bytes": len(transcript.encode('utf-8')),
            "compressed_payload_bytes": payload_size,
            "total_wire_bytes": len(wire_bytes),
            "compression_ratio": round(len(transcript.encode('utf-8')) / max(payload_size, 1), 2),
            "semantic_inference_time_ms": round(t_infer_ms, 3),
            "framing_time_ms": round(t_frame_ms, 3),
            "total_processing_time_ms": round(t_total_ms, 3),
            "confidence": round(sem_res.confidence, 3),
            "fallback_used": sem_res.is_fallback,
        }

        return EncodedSemanticPacket(
            serialized_bytes=wire_bytes,
            compression_tier=sem_res.compression_tier,
            payload_size=payload_size,
            semantic_result=sem_res,
            priority=p_level,
            source_language=source_language,
            target_language=target_language,
            sequence_number=sequence,
            telemetry=telemetry
        )

    def decode_packet(
        self,
        wire_bytes: bytes,
        target_language: str = "en"
    ) -> DecodedSemanticMessage:
        t_start = time.perf_counter()

        # 1. Parse & validate CRC
        packet = packet_framer.parse_and_validate_frame(wire_bytes)
        crc_valid = True

        prosody = packet.prosody_vector if packet.prosody_vector else bytes(16)

        # 2. Decompress semantic payload
        sem_res = semantic_compressor.decompress(packet.compressed_payload)
        sem_res.prosody_vector = prosody

        # 3. Realize into target language
        decoded_text = translation_engine.realize(sem_res, target_language)
        t_decode_ms = (time.perf_counter() - t_start) * 1000

        return DecodedSemanticMessage(
            decoded_text=decoded_text,
            source_language=packet.source_language,
            target_language=target_language,
            priority=packet.priority,
            urgency=sem_res.urgency,
            semantic_result=sem_res,
            prosody_vector=prosody,
            crc_valid=crc_valid,
            decode_time_ms=t_decode_ms
        )


def process_transcript(
    transcript: str,
    source_language: str = "en",
    target_language: str = "en",
    prosody_vector: Optional[bytes] = None,
    callsign: str = "CMD_ALPHA",
    sequence: int = 1,
    priority: int = -1
) -> EncodedSemanticPacket:
    return Member3Engine.get_instance().process_transcript(
        transcript, source_language, target_language, prosody_vector, callsign, sequence, priority
    )

def decode_packet(
    wire_bytes: bytes,
    target_language: str = "en"
) -> DecodedSemanticMessage:
    return Member3Engine.get_instance().decode_packet(wire_bytes, target_language)
