# hybrid_engine.py
"""
iTantra M3 — Hybrid Semantic Parsing & Ambiguity Resolution Layer
Combines deterministic baseline codebook rules with lightweight TinyML
Contextual Semantic Role Classification for robust disambiguation of
unseen proper nouns, callsigns, quantities, resources, hazards, and statuses.
"""

import re
from typing import List, Tuple, Optional, Dict
from semantic_schema import (
    SemanticMessage, SemanticField,
    Action, Urgency, Entity, Target, Condition, Emotion
)
import semantic_parser
from tinyml_classifier import TinyMLClassifier

_DIRECTION_WORDS = {"east", "west", "north", "south", "northeast", "northwest", "southeast", "southwest"}


def _extract_candidate_spans(text: str) -> List[Dict]:
    """
    Extract candidate spans and their left/right contexts for TinyML classification.
    """
    candidates = []
    text_len = len(text)

    # 1. Callsign/Identifier candidates (e.g. "Alpha 12", "Sector 4", "Unit Alpha 7", "Team 3")
    for m in re.finditer(r'\b(?:team\s+|unit\s+|squad\s+)?([a-zA-Z]+\s+\d+)\b', text, re.IGNORECASE):
        span = m.group(0).strip()
        candidates.append({
            "span": span,
            "left_ctx": text[:m.start()].strip(),
            "right_ctx": text[m.end():].strip(),
            "type_hint": "CALLSIGN_OR_LOC",
        })

    # 2. Proper noun / prepositional location candidates (e.g. "to Green Valley Hospital", "toward the old railway bridge", "near Nagpur", "to Xyzgarh")
    prep_patterns = [
        re.compile(r'(?i:\b(?:to|at|in|near|around|toward|towards|from|behind)\s+(?:the\s+)?)([a-zA-Z0-9\u0900-\u097F]{2,}(?:\s+[a-zA-Z0-9\u0900-\u097F]+){0,3})\b'),
        re.compile(r'(?:(?:एक|दो|तीन|चार|पांच|पाच|पाँच)\s+लोग\s+)?([\u0900-\u097Fa-zA-Z]{2,}(?:\s+[\u0900-\u097Fa-zA-Z]+){0,3})\s+(?:के पास|की तरफ)'),
        re.compile(r'\b([A-Z][a-zA-Z]{2,}(?:\s+[a-zA-Z]+){0,2})\s+(?i:control|base|hq|post|command|hospital|station|bridge|road)\b'),
    ]
    stopwords_set = {"immediately", "now", "right", "please", "urgent", "fast", "asap", "and", "but", "so", "because", "send", "the", "people", "everyone", "we", "they"}
    for pattern in prep_patterns:
        for m in pattern.finditer(text):
            raw_span = m.group(1).strip()
            # Clean trailing stopwords
            words = raw_span.split()
            while words and words[-1].lower() in stopwords_set:
                words.pop()
            while words and words[0].lower() in stopwords_set:
                words.pop(0)
            if words:
                span = " ".join(words)
                if len(span) >= 2:
                    candidates.append({
                        "span": span,
                        "left_ctx": text[:m.start(1)].strip(),
                        "right_ctx": text[m.end(1):].strip(),
                        "type_hint": "LOCATION",
                    })

    # 3. Hazard & event candidates (e.g. "unsafe", "building collapsed", "dangerous", "fire", "தீ விபத்து")
    for m in re.finditer(r'\b(unsafe|dangerous|building collapsed|collapsed|structure failed|fire|flood|landslide|toxic|explosion|தீ விபத்து|आग|बाढ़)\b', text, re.IGNORECASE):
        span = m.group(0).strip()
        candidates.append({
            "span": span,
            "left_ctx": text[:m.start()].strip(),
            "right_ctx": text[m.end():].strip(),
            "type_hint": "HAZARD",
        })

    # 4. Status / communication link candidates
    for m in re.finditer(r'\b(signal is weak|communication link is active|communication link is still active|link is active|link is down|signal is weak and noisy|comms active|comms down)\b', text, re.IGNORECASE):
        span = m.group(0).strip()
        candidates.append({
            "span": span,
            "left_ctx": text[:m.start()].strip(),
            "right_ctx": text[m.end():].strip(),
            "type_hint": "STATUS",
        })

    # 5. Resource candidates (e.g. "ambulance", "medical team", "rescue workers", "help", "support", "oxygen cylinders")
    for m in re.finditer(r'\b(ambulance|medical team|rescue workers|rescue team|help|support|assistance|medicines|oxygen cylinders|fire brigade|மருத்துவ உதவி|मदद)\b', text, re.IGNORECASE):
        span = m.group(0).strip()
        candidates.append({
            "span": span,
            "left_ctx": text[:m.start()].strip(),
            "right_ctx": text[m.end():].strip(),
            "type_hint": "RESOURCE",
        })

    # 6. Emotion candidates (e.g. "terrified", "panicking", "frightened", "scared", "in distress", "fear")
    for m in re.finditer(r'\b(terrified|panicking|panicked|scared|frightened|fear|distress|in distress|घबराए हुए|பீதியடைந்த)\b', text, re.IGNORECASE):
        span = m.group(0).strip()
        candidates.append({
            "span": span,
            "left_ctx": text[:m.start()].strip(),
            "right_ctx": text[m.end():].strip(),
            "type_hint": "EMOTION",
        })

    # 7. Direction candidates (e.g. "east", "west", "north", "south")
    for m in re.finditer(r'\b(east|west|north|south|northeast|northwest|southeast|southwest|eastern|western|northern|southern)\b', text, re.IGNORECASE):
        span = m.group(0).strip()
        candidates.append({
            "span": span,
            "left_ctx": text[:m.start()].strip(),
            "right_ctx": text[m.end():].strip(),
            "type_hint": "DIRECTION",
        })

    return candidates


def parse(text: str, language: str = "en") -> SemanticMessage:
    """
    Execute Hybrid Semantic Parsing:
    1. Runs baseline parser rules.
    2. Runs TinyML contextual classifier on ambiguous spans.
    3. Fuses predictions and preserves raw text for unseen proper nouns.
    """
    # 1. Baseline parse (language is threaded through for source-language context)
    msg = semantic_parser._parse_core(text, language)

    # 2. Extract candidate spans for TinyML resolution
    candidates = _extract_candidate_spans(text)
    clf = TinyMLClassifier.get_instance()

    seen_roles = set()
    for cand in candidates:
        span = cand["span"]
        left = cand["left_ctx"]
        right = cand["right_ctx"]

        role, conf = clf.predict_role(span=span, left_ctx=left, right_ctx=right, full_text=text)

        # High confidence threshold for TinyML resolution
        if conf >= 0.70 and role != "UNKNOWN":
            # --- CALLSIGN DISAMBIGUATION ---
            if role == "CALLSIGN":
                clean_cs = re.sub(r'^(team|unit|squad)\s+', '', span, flags=re.IGNORECASE).strip()
                # Check if already present in extra_fields
                existing_cs = [f for f in msg.extra_fields if f.name == "CALLSIGN"]
                if not existing_cs:
                    msg.extra_fields.append(SemanticField("CALLSIGN", clean_cs, 0, span, "TEXT", conf, "TINYML"))
                    if "CALLSIGN" not in msg.matched_fields:
                        msg.matched_fields.append("CALLSIGN")
                # Cleanse quantity if it was contaminated by callsign digits
                if msg.quantity.code > 0:
                    digits = re.findall(r'\b\d+\b', span)
                    if digits and int(digits[0]) == msg.quantity.code:
                        # Re-detect true quantity without the callsign
                        scrubbed_qty = semantic_parser._detect_quantity(text.lower(), text)
                        if scrubbed_qty is not None:
                            msg.quantity = SemanticField("QUANTITY", scrubbed_qty, scrubbed_qty, str(scrubbed_qty), source_type="HYBRID")
                        else:
                            msg.quantity = SemanticField("QUANTITY", 0, 0, source_type="HYBRID")

            # --- LOCATION / PROPER NOUN DISAMBIGUATION ---
            elif role == "LOCATION":
                # Prefer exact text preservation, and don't overwrite a longer location with a sub-span
                if not msg.location_text or len(span) >= len(msg.location_text):
                    msg.target = SemanticField(
                        "TARGET", Target.PROPER_LOCATION.name, Target.PROPER_LOCATION.value,
                        span, "PROPER_NOUN", conf, "TINYML"
                    )
                    msg.location_text = span
                    msg.location_source = "TINYML"
                    if "TARGET" not in msg.matched_fields:
                        msg.matched_fields.append("TARGET")
                    if "LOCATION" not in msg.matched_fields:
                        msg.matched_fields.append("LOCATION")

            # --- RESOURCE DISAMBIGUATION ---
            elif role == "RESOURCE":
                span_lower = span.lower()
                if "ambulance" in span_lower and msg.entity.code == 0:
                    msg.entity = SemanticField("ENTITY", Entity.AMBULANCE.name, Entity.AMBULANCE.value, span, source_type="TINYML")
                    if "ENTITY" not in msg.matched_fields:
                        msg.matched_fields.append("ENTITY")
                elif "medical" in span_lower and msg.entity.code == 0:
                    msg.entity = SemanticField("ENTITY", Entity.MEDICAL.name, Entity.MEDICAL.value, span, source_type="TINYML")
                    if "ENTITY" not in msg.matched_fields:
                        msg.matched_fields.append("ENTITY")
                else:
                    # Multiple resources or generic resource
                    if span_lower in {"support", "help", "assistance"} and msg.entity.code != 0:
                        pass
                    else:
                        existing_res = [f for f in msg.extra_fields if f.name == "RESOURCE_REQUIRED" and f.source_phrase.lower() == span_lower]
                        if not existing_res:
                            if not msg.resource_text:
                                msg.resource_text = span
                                msg.resource_source = "TINYML"
                            elif span_lower != msg.resource_text.lower():
                                msg.extra_fields.append(SemanticField("RESOURCE_REQUIRED", span, 0, span, "TEXT", conf, "TINYML"))
                            if "RESOURCE" not in msg.matched_fields:
                                msg.matched_fields.append("RESOURCE")

            # --- HAZARD DISAMBIGUATION ---
            elif role == "HAZARD":
                if not msg.hazard_text:
                    msg.hazard_text = span
                    msg.hazard_source = "TINYML"
                elif span.lower() not in msg.hazard_text.lower():
                    msg.hazard_text = f"{msg.hazard_text}, {span}"
                if "HAZARD" not in msg.matched_fields:
                    msg.matched_fields.append("HAZARD")

            # --- STATUS DISAMBIGUATION ---
            elif role == "STATUS":
                if not msg.status_text:
                    msg.status_text = span
                    msg.status_source = "TINYML"
                elif span.lower() not in msg.status_text.lower():
                    msg.status_text = f"{msg.status_text}, {span}"
                if "STATUS" not in msg.matched_fields:
                    msg.matched_fields.append("STATUS")

            # --- DIRECTION DISAMBIGUATION ---
            elif role == "DIRECTION":
                existing_dir = [f for f in msg.extra_fields if f.name == "DIRECTION"]
                if not existing_dir:
                    msg.extra_fields.append(SemanticField("DIRECTION", span.upper(), 0, span, "TEXT", conf, "TINYML"))
                    if "DIRECTION" not in msg.matched_fields:
                        msg.matched_fields.append("DIRECTION")

            # --- EMOTION DISAMBIGUATION ---
            elif role == "EMOTION":
                span_lower = span.lower()
                if "terrified" in span_lower or "panic" in span_lower or "frightened" in span_lower or "scared" in span_lower:
                    msg.emotion = SemanticField("EMOTION", Emotion.PANIC.name, Emotion.PANIC.value, span, confidence=conf, source_type="TINYML")
                elif "distress" in span_lower:
                    msg.emotion = SemanticField("EMOTION", Emotion.DISTRESS.name, Emotion.DISTRESS.value, span, confidence=conf, source_type="TINYML")
                if "EMOTION" not in msg.matched_fields:
                    msg.matched_fields.append("EMOTION")

    # Safety validation: populate failed_fields
    failed = []
    if msg.action.code == 0:
        failed.append("ACTION")
    if msg.target.code == 0 and not msg.location_text:
        failed.append("TARGET")
    if msg.entity.code == 0 and msg.action.code == Action.SEND_TEAM.value and not msg.resource_text:
        failed.append("ENTITY")
    msg.failed_fields = failed

    meaningful = semantic_parser._meaningful_field_count(msg)
    has_status = semantic_parser._has_status_content(text.lower()) or bool(msg.status_text) or bool(msg.hazard_text)

    # If meaningful content is extracted, return semantic message
    if meaningful < 2 and not has_status:
        reason = f"Insufficient semantic content. Recognised fields: {', '.join(msg.matched_fields) or 'none'}"
        return SemanticMessage(
            fallback_text=text,
            fallback_reason=reason,
            matched_fields=msg.matched_fields,
            failed_fields=failed,
        )

    return msg
