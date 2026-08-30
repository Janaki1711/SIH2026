# semantic_parser.py
"""
iTantra M3 Semantic Parser
Converts natural language into a SemanticMessage, capturing deep inspection data.
"""

import re
from semantic_schema import SemanticMessage, SemanticField, Action, Urgency, Entity, Target, Condition, Emotion

def parse_english(text: str) -> SemanticMessage:
    text_lower = text.lower()
    msg = SemanticMessage()
    matched = []
    
    # Target
    if "hubbli" in text_lower:
        msg.target = SemanticField("TARGET", Target.HUBBLI.name, Target.HUBBLI.value, "hubbli")
        matched.append("TARGET")
    elif "tolankere" in text_lower:
        msg.target = SemanticField("TARGET", Target.TOLANKERE.name, Target.TOLANKERE.value, "tolankere")
        matched.append("TARGET")
    elif "sector 1" in text_lower or "sector one" in text_lower:
        msg.target = SemanticField("TARGET", Target.SECTOR_1.name, Target.SECTOR_1.value, "sector 1")
        matched.append("TARGET")
    elif "sector 4" in text_lower or "sector four" in text_lower:
        msg.target = SemanticField("TARGET", Target.SECTOR_4.name, Target.SECTOR_4.value, "sector 4")
        matched.append("TARGET")
        
    # Entity
    if "rescue" in text_lower:
        msg.entity = SemanticField("ENTITY", Entity.RESCUE.name, Entity.RESCUE.value, "rescue")
        matched.append("ENTITY")
    elif "medical" in text_lower or "doctor" in text_lower:
        msg.entity = SemanticField("ENTITY", Entity.MEDICAL.name, Entity.MEDICAL.value, "medical")
        matched.append("ENTITY")
    elif "police" in text_lower:
        msg.entity = SemanticField("ENTITY", Entity.POLICE.name, Entity.POLICE.value, "police")
        matched.append("ENTITY")
    elif "fire" in text_lower:
        msg.entity = SemanticField("ENTITY", Entity.FIRE.name, Entity.FIRE.value, "fire")
        matched.append("ENTITY")
    elif "supply" in text_lower:
        msg.entity = SemanticField("ENTITY", Entity.SUPPLY.name, Entity.SUPPLY.value, "supply")
        matched.append("ENTITY")
        
    # Action
    if "send" in text_lower or "dispatch" in text_lower:
        msg.action = SemanticField("ACTION", Action.SEND_TEAM.name, Action.SEND_TEAM.value, "send")
        matched.append("ACTION")
    elif "help" in text_lower or "sos" in text_lower:
        msg.action = SemanticField("ACTION", Action.REQUEST_HELP.name, Action.REQUEST_HELP.value, "help")
        matched.append("ACTION")
    elif "evacuate" in text_lower:
        msg.action = SemanticField("ACTION", Action.EVACUATE.name, Action.EVACUATE.value, "evacuate")
        matched.append("ACTION")
        
    # Urgency
    if "immediately" in text_lower or "urgent" in text_lower or "critical" in text_lower or "sos" in text_lower:
        msg.urgency = SemanticField("URGENCY", Urgency.CRITICAL.name, Urgency.CRITICAL.value, "immediately/urgent")
        matched.append("URGENCY")
    elif "fast" in text_lower:
        msg.urgency = SemanticField("URGENCY", Urgency.HIGH.name, Urgency.HIGH.value, "fast")
        matched.append("URGENCY")
        
    # Condition & Emotion (From Prompt Example)
    if "trapped" in text_lower:
        msg.condition = SemanticField("CONDITION", Condition.TRAPPED.name, Condition.TRAPPED.value, "trapped")
        matched.append("CONDITION")
    if "distress" in text_lower or "distressed" in text_lower:
        msg.emotion = SemanticField("EMOTION", Emotion.DISTRESS.name, Emotion.DISTRESS.value, "distress")
        matched.append("EMOTION")
        
    # Quantity
    nums = re.findall(r'\b(one|two|three|four|five|\d+)\b', text_lower)
    if nums:
        mapping = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
        val = int(nums[0]) if nums[0].isdigit() else mapping.get(nums[0], 1)
        msg.quantity = SemanticField("QUANTITY", val, val, nums[0])
        matched.append("QUANTITY")
    elif msg.action.value == Action.SEND_TEAM.name:
        msg.quantity = SemanticField("QUANTITY", 1, 1, "implied one")
        matched.append("QUANTITY")

    msg.matched_fields = matched
    return msg

def parse_hindi(text: str) -> SemanticMessage:
    text_lower = text.lower()
    msg = SemanticMessage()
    matched = []
    
    if "hubbli" in text_lower or "हब्बली" in text:
        msg.target = SemanticField("TARGET", Target.HUBBLI.name, Target.HUBBLI.value, "हब्बली/hubbli")
        matched.append("TARGET")
    elif "tolankere" in text_lower or "तोलनकेरे" in text:
        msg.target = SemanticField("TARGET", Target.TOLANKERE.name, Target.TOLANKERE.value, "तोलनकेरे/tolankere")
        matched.append("TARGET")
        
    if "rescue" in text_lower or "बचाव" in text:
        msg.entity = SemanticField("ENTITY", Entity.RESCUE.name, Entity.RESCUE.value, "बचाव/rescue")
        matched.append("ENTITY")
    elif "medical" in text_lower or "चिकित्सा" in text:
        msg.entity = SemanticField("ENTITY", Entity.MEDICAL.name, Entity.MEDICAL.value, "चिकित्सा/medical")
        matched.append("ENTITY")
        
    if "send" in text_lower or "भेजो" in text or "भेजें" in text:
        msg.action = SemanticField("ACTION", Action.SEND_TEAM.name, Action.SEND_TEAM.value, "भेजो/send")
        matched.append("ACTION")
    elif "help" in text_lower or "मदद" in text or "sos" in text_lower:
        msg.action = SemanticField("ACTION", Action.REQUEST_HELP.name, Action.REQUEST_HELP.value, "मदद/help")
        matched.append("ACTION")
        
    if "immediately" in text_lower or "तुरंत" in text or "sos" in text_lower:
        msg.urgency = SemanticField("URGENCY", Urgency.CRITICAL.name, Urgency.CRITICAL.value, "तुरंत/immediately")
        matched.append("URGENCY")
        
    if "एक" in text or "1" in text or "one" in text_lower:
        msg.quantity = SemanticField("QUANTITY", 1, 1, "एक")
        matched.append("QUANTITY")
    elif "दो" in text or "2" in text or "two" in text_lower:
        msg.quantity = SemanticField("QUANTITY", 2, 2, "दो")
        matched.append("QUANTITY")
    elif msg.action.value == Action.SEND_TEAM.name:
        msg.quantity = SemanticField("QUANTITY", 1, 1, "implied one")
        matched.append("QUANTITY")
        
    msg.matched_fields = matched
    return msg

def parse(text: str, language: str) -> SemanticMessage:
    """Parse text into a SemanticMessage."""
    if language == "en":
        msg = parse_english(text)
    elif language == "hi":
        msg = parse_hindi(text)
    else:
        msg = SemanticMessage()

    # Determine if this needs to fallback
    failed = []
    if msg.action.code == 0: failed.append("ACTION")
    if msg.target.code == 0: failed.append("TARGET")
    if msg.entity.code == 0 and msg.action.code == Action.SEND_TEAM.value: failed.append("ENTITY")
    
    msg.failed_fields = failed

    # If missing core fields, trigger fallback
    if "ACTION" in failed or "TARGET" in failed:
        reason = f"Required field(s) not recognized: {', '.join(failed)}"
        return SemanticMessage(fallback_text=text, fallback_reason=reason, matched_fields=msg.matched_fields, failed_fields=failed)
        
    return msg
