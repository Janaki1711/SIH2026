# semantic_parser.py
"""
iTantra M3 Semantic Parser — Enhanced Hybrid Recognition Layer v2
Converts natural language into a SemanticMessage.

Fixes in v2:
  - Callsign/identifier numbers (Alpha 7, Sector 4) no longer parsed as QUANTITY
  - Fallback only when truly nothing semantic can be extracted (≥2 of 5 core fields empty)
  - "fire has broken out" → ACTION=ALERT, not stuck as ENTITY=FIRE
  - Proper nouns detected at sentence-start (e.g. "Nagpur control, ...")
  - Hindi/Indic word boundary fix (Unicode substring match)
  - Multi-condition extraction (injured AND unconscious preserved)
  - "need an ambulance" → REQUEST_HELP
  - Phrase-level conflict guards (fire team ≠ fire hazard)
  - Tamil spelling variants for Hubbli
  - Communication status recognised (stops spurious fallback)
  - Translation engine never emits literal "UNKNOWN" — uses source_phrase fallback
"""

import re
from typing import Optional, Tuple, List
from semantic_schema import (
    SemanticMessage, SemanticField,
    Action, Urgency, Entity, Target, Condition, Emotion
)

# ─────────────────────────────────────────────
#  CALLSIGN / IDENTIFIER GUARD
#  Numbers inside these patterns are NOT quantities
# ─────────────────────────────────────────────
# Matches: "Alpha 7", "Bravo 3", "Team 2", "Sector 4", "Unit 5", "Grid 12"
_CALLSIGN_RE = re.compile(
    r'\b(alpha|bravo|charlie|delta|echo|foxtrot|team|unit|grid|post|squad|'
    r'group|callsign|sector|zone|block|phase|route|road|highway|nh|sh)\s+\d+\b',
    re.IGNORECASE
)

def _scrub_callsign_numbers(text: str) -> str:
    """Replace digits inside callsigns/identifiers with a placeholder so they
    are not picked up by the quantity extractor."""
    return _CALLSIGN_RE.sub(lambda m: re.sub(r'\d+', 'NUM_SCRUBBED', m.group()), text)


# ─────────────────────────────────────────────
#  HYBRID CODEBOOK TABLES  (keyword → enum)
#  Ordered: most-specific phrase FIRST to avoid
#  "fire team" → Entity.FIRE before Entity.FIRE_TEAM
# ─────────────────────────────────────────────

# ACTION phrases
ACTION_MAP = [
    (Action.SEND_TEAM, [
        "send", "dispatch", "deploy", "rush", "forward", "transmit",
        "भेजो", "भेजें", "तैनात", "भेज",
        "पाठवा", "धाड",
        "મોકલો", "મોકલોને", "રવાના કરો",
        "ಅയക്കുക", "അയക്കൂ", "നിയോഗിക്കുക",
        "ପଠାନ୍ତୁ", "ପଠାଅ", "ନିୟୋଜିତ କରନ୍ତୁ",
        "পাঠান", "পাঠাও", "প্রেরণ করুন",
        "அனுப்பு", "அனுப்பவும்", "அனுப்புங்கள்",
        "పంపు", "పంపండి",
        "ಕಳುಹಿಸಿ", "ಕಳಿಸಿ",
    ]),
    (Action.REQUEST_HELP, [
        "help", "sos", "mayday", "assist", "need help", "call for help",
        "we need", "need an", "need a", "require", "requesting",
        "मदद", "सहायता", "बचाओ", "भेजो",
        "मदत", "वाचवा",
        "મદદ", "સહાય", "બચાવો",
        "സഹായം", "രക്ഷിക്കൂ", "സഹായിക്കൂ",
        "ସାହାଯ୍ୟ", "ରକ୍ଷା କର", "ମଦତ",
        "সাহায্য", "বাঁচাও", "সাহায্যের প্রয়োজন",
        "உதவி", "காப்பாற்று",
        "సహాయం",
        "ಸಹಾಯ", "ರಕ್ಷಿಸಿ",
    ]),
    (Action.EVACUATE, [
        "evacuate", "evacuation", "clear the area", "move out", "withdraw",
        "खाली करो", "निकालो",
        "रिकामे करा",
        "ખાલી કરો", "ખાલી કરાવો",
        "ഒഴിപ്പിക്കുക", "ഒഴിവാക്കുക",
        "ଖାଲି କରନ୍ତୁ", "ବାହାର କରନ୍ତୁ",
        "খালি করুন", "সরিয়ে নিন",
        "வெளியேற்று",
        "తరలించు",
        "ಖಾಲಿ ಮಾಡಿ",
    ]),
    (Action.ALERT, [
        "broken out", "outbreak", "alert", "warn", "warning", "beware",
        "danger ahead", "has broken", "broke out",
        "चेतावनी", "इशारा",
        "ચેતવણી",
        "മുന്നറിയിപ്പ്",
        "ଚେତାବନୀ",
        "সতর্কতা",
        "எச்சரிக்கை",
        "హెచ్చరించు",
        "ಎಚ್ಚರಿಕೆ",
    ]),
    (Action.SEARCH, [
        "search", "find", "locate", "look for", "sweep",
        "खोजो", "ढूंढो",
        "शोधा", "શોધો",
        "അന്വേഷിക്കുക",
        "ଖୋଜନ୍ତୁ", "খোঁজো",
        "தேடு",
        "వెతుకు",
        "ಹುಡುಕಿ",
    ]),
    (Action.MOVE, [
        "moving", "advance", "proceeding", "heading", "going to", "towards",
        "आगे बढ़", "चल रहा", "जा रहा",
        "जात आहे", "पुढे जा",
        "આગળ વધો",
        "മുന്നേറുന്നു",
        "ଏଗିରନ୍ତୁ", "এগিয়ে যাচ্ছে",
        "நகர்கிறது",
        "కదులుతున్నాడు",
        "ಚಲಿಸುತ್ತಿದ್ದಾರೆ",
    ]),
    (Action.REPORT, [
        "report", "status update", "inform", "notify", "update",
        "रिपोर्ट", "सूचना", "अहवाल",
        "અહેવાલ",
        "റിപ്പോർട്ട്",
        "ରିପୋର୍ଟ", "রিপোর্ট",
        "அறிக்கை",
        "నివేదించు",
        "ವರದಿ",
    ]),
    (Action.HOLD, [
        "hold", "stop", "halt", "wait", "stand by",
        "रुको", "थांबा",
        "થંભો",
        "നിൽക്കൂ", "നിർത്തുക",
        "ଅଟକନ୍ତୁ", "ରୁହନ୍ତୁ", "থামুন",
        "நிறுத்து", "ఆగు", "ನಿಲ್ಲಿಸಿ",
    ]),
    (Action.SECURE, [
        "secure", "lock down", "seal", "contain",
        "सुरक्षित करो", "सुरक्षित करा",
        "સુરક્ષિત કરો",
        "സുരക്ഷിതമാക്കുക",
        "ସୁରକ୍ଷିତ କରନ୍ତୁ", "নিরাপদ করুন",
        "பாதுகாக்க", "భద్రపరచు", "ಸುರಕ್ಷಿತಗೊಳಿಸಿ",
    ]),
]

# ENTITY phrases — most-specific first to prevent "fire team" → FIRE
ENTITY_MAP = [
    (Entity.FIRE_TEAM, [
        "fire team", "fire brigade", "fire fighter", "fireman", "fire department",
        "अग्निशमन", "फायर ब्रिगेड",
        "અગ્નિશમન દળ",
        "അഗ്നിശമന സേന",
        "ଅଗ୍ନିଶମ ଦଳ", "দমকল দল",
        "தீயணைப்பு", "అగ్నిమాపక", "ಅಗ್ನಿಶಾಮಕ",
    ]),
    (Entity.AMBULANCE, [
        "ambulance", "एम्बुलेंस", "रुग्णवाहिका",
        "એમ્બ્યુલન્સ",
        "ആംബുലൻസ്",
        "ଆମ୍ବୁଲାନ୍ସ", "অ্যাম্বুলেন্স",
        "ஆம்புலன்ஸ்", "అంబులెన్స్", "ಆಂಬ್ಯುಲೆನ್ಸ್",
    ]),
    (Entity.MEDICAL, [
        "medical", "doctor", "nurse", "paramedic", "medic", "health team",
        "चिकित्सा", "डॉक्टर", "वैद्य",
        "તબીબ",
        "വൈദ്യൻ",
        "ଡାକ୍ତର", "ডাক্তার",
        "மருத்துவம்", "மருத்துவ", "వైద్యం", "ವೈದ್ಯ",
    ]),
    (Entity.RESCUE, [
        "rescue", "rescue team", "save", "बचाव", "बचाव दल",
        "बचाव पथक",
        "બચાવ",
        "രക്ഷാസംഘം", "രക്ഷ",
        "ଉଦ୍ଧାର", "উদ্ধার",
        "மீட்பு", "రక్షణ", "ರಕ್ಷಣಾ",
    ]),
    (Entity.POLICE, [
        "police", "law enforcement", "cops", "officer",
        "पुलिस", "पोलिस",
        "પોલીસ",
        "പോലീസ്",
        "ପୋଲିସ", "পুলিশ",
        "காவல்துறை", "పోలీసు", "ಪೊಲೀಸ್",
    ]),
    (Entity.HELICOPTER, [
        "helicopter", "chopper", "helo", "heli", "हेलिकॉप्टर",
        "હેલિકોપ્ટર",
        "ഹെലികോപ്ടർ",
        "ହେଲିକପ୍ଟର", "হেলিকপ্টার",
        "ஹெலிகாப்டர்", "హెలికాప్టర్", "ಹೆಲಿಕಾಪ್ಟರ್",
    ]),
    (Entity.ENGINEER, ["engineer", "engineering team", "sapper", "tech team"]),
    (Entity.SUPPLY, [
        "supply", "supplies", "ration", "relief",
        "आपूर्ति", "रसद", "आपूर्ती",
        "સામાન",
        "സാമഗ്രി",
        "ସାମଗ୍ରୀ", "সরবরাহ",
        "సరఫరా", "ಸರಬರಾಜು",
    ]),
    (Entity.TROOP, [
        "troop", "troops", "soldier", "soldiers", "military", "army",
        "सेना", "जवान",
        "સૈન્ય",
        "സൈന്യം",
        "ସୈନ୍ୟ", "সেনা",
        "படை", "సైనికులు", "ಸೈನಿಕ",
    ]),
    (Entity.DISASTER, ["disaster", "relief team", "disaster team", "आपदा",
                       "આપત્તિ", "വിപത്ത്", "ବିପର୍ଯ୍ୟାୟ", "দুর্যোগ",
                       "பேரிடர்", "విపత్తు", "ವಿಪತ್ತು"]),
    # FIRE last — only match standalone "fire" when not part of "fire team/brigade"
    (Entity.FIRE, [
        "fire", "blaze", "flames", "burning",
        "आग", "अग्नि", "தீ", "అగ్ని", "ಬೆಂಕಿ",
    ]),
]

# KNOWN TARGET locations — order by specificity (longer phrases first)
TARGET_MAP = [
    (Target.HUBBLI,    [
        "hubbli", "hubli", "hübli",
        "हब्बली", "हुबली",
        "હબ્બલી", "હૂબલી",
        "ഹുബ്ലി", "ഹുബ്ബള്ളി",
        "ହୁବ୍ଲି", "ହୁବଳୀ",
        "হুবলি", "হুব্বাল্লি",
        "ஹூப்ளி", "ஹுப்பள்ளி", "ஹுப்பளி",
        "హుబ్లి", "హుబ్లీ", "ಹುಬ್ಬಳ್ಳಿ",
    ]),
    (Target.TOLANKERE, [
        "tolankere", "तोलनकेरे",
        "તોલનકેરે", "તોલાનકેરે",
        "തോളങ്കരെ", "തൊലങ്കരെ",
        "ତୋଲାଙ୍କେରେ", "ତୋଲନକେରେ",
        "তোলনকেরে", "তোলাঙ্কেরে",
        "தோலன்கெரே", "తోలంకెరె", "ತೊಳನಕೆರೆ",
    ]),
    (Target.BASE,      [
        "base camp", "base", "hq", "headquarters",
        "बेस", "आधार", "मुख्यालय",
    ]),
    (Target.SECTOR_1,  ["sector 1", "sector one", "सेक्टर 1", "सेक्टर एक"]),
    (Target.SECTOR_2,  ["sector 2", "sector two", "सेक्टर 2", "सेक्टर दो"]),
    (Target.SECTOR_3,  ["sector 3", "sector three", "सेक्टर 3", "सेक्टर तीन"]),
    (Target.SECTOR_4,  [
        "sector 4", "sector four", "सेक्टर 4", "सेक्टर चार",
        "సెక్టర్ 4", "ಸೆಕ್ಟರ್ 4",
    ]),
    (Target.SECTOR_5,  ["sector 5", "sector five"]),
    (Target.BRIDGE,    [
        "old bridge", "bridge", "पुल", "सेतु", "பாலம்", "వంతెన", "ಸೇತುವೆ",
    ]),
    (Target.HOSPITAL,  [
        "hospital", "clinic", "अस्पताल", "हॉस्पिटल",
        "மருத்துவமனை", "ఆసుపత్రి", "ಆಸ್ಪತ್ರೆ",
    ]),
    (Target.SCHOOL,    ["school", "स्कूल", "பள்ளி", "పాఠశాల", "ಶಾಲೆ"]),
]

# URGENCY phrases
URGENCY_MAP = [
    (Urgency.CRITICAL, [
        "immediately", "immediate", "urgent", "urgently", "critical", "sos",
        "asap", "right now", "right away", "now", "emergency", "at once", "straight away",
        "તાત્કાલિક", "અત્યાવશ્યક",
        "ഉടൻ", "അടിയന്തരം",
        "ତୁରନ୍ତ", "ଜରୁରୀ",
        "জরুরি", "দ্রুত",
        "तुरंत", "फौरन", "अभी", "जरूरी", "आपातकाल",
        "ताबडतोब", "तात्काळ",
        "உடனடியாக", "இப்போதே",
        "వెంటనే", "అత్యవసరం",
        "ತಕ್ಷಣ", "ತುರ್ತು",
    ]),
    (Urgency.HIGH, [
        "fast", "quickly", "quick", "hurry", "soon", "rapidly",
        "જલ્દી",
        "വേഗം", "ശീଘ്രം",
        "ଶୀଘ୍ର",
        "তাড়াতাড়ি",
        "जल्दी", "शीघ्र", "लवकर", "விரைவாக", "త్వరగా", "ಬೇಗ",
    ]),
    (Urgency.MEDIUM, ["when possible", "moderate", "जब संभव हो"]),
    (Urgency.LOW,    ["low priority", "routine", "normal", "साधारण"]),
]

# CONDITION phrases — extract ALL matching conditions, not just first
CONDITION_MAP = [
    (Condition.TRAPPED,     [
        "trapped", "stuck", "pinned", "buried", "caught", "cannot escape",
        "ફસાયેલા", "અટકેલા",
        "अडकले",
        "കുടുങ്ങി",
        "ଫସି",
        "আটকে",
        "फंसे", "फंसा", "फँसलेले", "சிக்கியிருக்கிறார்கள்",
        "చిక్కుకున్నారు", "ಸಿಕ್ಕಿಕೊಂಡಿದ್ದಾರೆ",
    ]),
    (Condition.INJURED,     [
        "injured", "hurt", "wound", "wounded", "bleeding", "fracture",
        "ઘાયલ",
        "പരിക്പറ്റി",
        "ଆହତ",
        "আহত",
        "घायल", "जख्मी", "चोट", "जखमी",
        "காயமடைந்தவர்கள்", "గాయపడిన", "ಗಾಯಗೊಂಡ",
    ]),
    (Condition.UNCONSCIOUS, [
        "unconscious", "unresponsive", "passed out", "fainted", "coma",
        "બેહોશ",
        "ബോധരഹിത",
        "ବେହୋସ",
        "অচেতন",
        "बेहोश", "अचेत", "बेशुद्ध",
        "மயக்கமடைந்தவர்கள்", "స్పృహ లేని", "ಅಪ್ರಜ್ಞಾವಸ್ಥೆ",
    ]),
    (Condition.MISSING,     [
        "missing", "lost", "not found", "disappeared", "unaccounted",
        "ગુમ થયા",
        "കാണാതായ",
        "ହଜି",
        "নিখোঁজ",
        "लापता", "गायब", "खोया", "बेपत्ता",
        "காணாமல்போனவர்கள்", "తప్పిపోయిన", "ಕಾಣೆಯಾಗಿದ್ದಾರೆ",
    ]),
    (Condition.CRITICAL,    [
        "critical condition", "life threatening", "very serious", "in danger",
        "ગંભીર",
        "ഗુરુતર",
        "ଗୁରୁତର",
        "গুরুতর",
        "गंभीर", "गंभीर अवस्था", "ஆபத்தான நிலை",
        "ప్రాణాపాయ స్థితి", "ಅಪಾಯಕರ ಸ್ಥಿತಿ",
    ]),
    (Condition.SAFE,        [
        "safe", "all clear", "rescued", "recovered",
        "सुरक्षित आहे",
        "સુરક્ષિત",
        "സുരക്ഷിത",
        "ସୁରକ୍ଷିତ",
        "নিরাপদ",
        "सुरक्षित है", "सुरक्षित हैं",
        "பாதுகாப்பாக", "సురక్షితంగா", "ಸುರಕ್ಷಿತ",
    ]),
    (Condition.EVACUATED,   [
        "evacuated", "cleared", "out of danger zone",
        "रिकामा केला",
        "ખાલી કરાયો",
        "ഒഴിപ്പിച്ച",
        "ଖାଲି ହୋଇଛି",
        "খালি করা হয়েছে",
        "निकाला गया", "बाहेर काढले",
    ]),
    (Condition.EXPOSED,     [
        "exposed", "stranded", "in the open", "no shelter",
        "ખુલ્લામાં",
        "അഭയമില്ല",
        "ଖୋଲା ସ୍ଥାନ",
        "খোলায়",
        "खुले में", "उघड्यावर",
    ]),
]

# EMOTION phrases
EMOTION_MAP = [
    (Emotion.PANIC, [
        "panic", "panicking", "panicked", "terrified", "terror", "petrified",
        "frantic", "hysterical", "out of control",
        "આતંકિત",
        "आतंकित",
        "ഭയചഞ്ചിത",
        "ଆତଙ୍କିତ",
        "আতঙ্কিত",
        "घबराना", "घबराए", "डर के मारे", "घाबरलेले", "भयभीत",
        "பீதியடைந்தவர்கள்", "భయాందోళనకు", "ಭಯಭೀತ",
    ]),
    (Emotion.DISTRESS, [
        "distress", "distressed", "desperate", "anguish", "in distress",
        "suffering", "agony", "helpless", "crying for help",
        "ત્રાસમાં",
        "त्रासात",
        "കഷ്ടത്തിൽ",
        "ଯନ୍ତ୍ରଣାରେ",
        "কষ্টে",
        "तकलीफ", "परेशान", "दुखी", "त्रास",
        "அவதிப்படுகிறார்கள்", "కష்టాల్లో", "ಸಂಕಷ್ಟದಲ್ಲಿ",
    ]),
    (Emotion.FEAR, [
        "fear", "fearful", "afraid", "frightened", "scared",
        "people are terrified", "everyone is terrified",
        "people are scared", "everyone is scared",
        "ડરથી",
        "भीती",
        "ഭയം",
        "ଭୟ",
        "ভয়",
        "डर", "भय", "घबराहट",
    ]),
    (Emotion.CONFUSION, [
        "confused", "disoriented", "chaos", "chaotic", "भ्रम", "अव्यवस्था",
        "ગૂંચવણ", "गोंधळ", "ആശയക്കുഴപ്പം", "ବିଭ୍ରାନ୍ତି", "বিভ্রান্তি",
    ]),
    (Emotion.CALM, [
        "calm", "stable", "controlled", "under control",
        "શાંત", "शांत", "ശാന്ത", "ଶାନ୍ତ", "শান্ত",
        "शांत", "அமைதியாக", "శాంతంగా", "ಶಾಂತ",
    ]),
    (Emotion.RELIEF, ["relieved", "safe now", "situation improved", "राहत", "दिलासा",
                      "રાહત", "ആശ്വാസ", "ଆଶ୍ଵାସ", "আশ্বাস"]),
]

# HAZARD keywords
HAZARD_KEYWORDS = [
    "fire", "flood", "earthquake", "landslide", "explosion", "gas leak",
    "chemical spill", "toxic", "radiation", "collapse", "tsunami", "cyclone",
    "sniper", "armed", "gunfire", "bomb", "mine", "threat", "dangerous",
    "building collapsed", "structure failed", "roof fallen",
    "आग", "बाढ़", "भूकंप", "विस्फोट",
    "தீ", "வெள்ளம்", "விபத்து",
    "అగ్ని", "వరదలు",
    "ಬೆಂಕಿ", "ಪ್ರವಾಹ",
    "આગ", "પૂર", "ભૂકંપ", "વિસ્ફોટ",
    "अग्निकांड", "भूस्खलन", "गैस रिसाव", "सुनामी", "चक्रवात",
    "തീപിടിത്തം", "പ്രളയം", "ഭൂകമ്പം", "ഉരുൾപൊട്ടൽ", "വിസ്ഫോടനം", "സുനാമി",
    "ଅଗ୍ନିକାଣ୍ଡ", "ବନ୍ୟା", "ଭୂକମ୍ପ", "ଭୂସ୍ଖଳନ", "ବିସ୍ଫୋରଣ", "ବାତ୍ୟା",
    "অগ্নিকাণ্ড", "বন্যা", "ভূমিকম্প", "ভূস্খলন", "বিস্ফোরণ", "ঘূর্ণিঝড়",
]

# RESOURCE keywords
RESOURCE_KEYWORDS = [
    "food", "water", "medicine", "blanket", "shelter", "tent",
    "oxygen", "blood", "equipment", "generator", "pump",
    "ખોરાક", "પાણી", "દવા", "મદદ",
    "अन्न", "औषध",
    "വിഭവം", "വെള്ളം", "മരുന്ന്",
    "ଖାଦ୍ୟ", "ପାଣି", "ଔଷଧ",
    "খাবার", "পানি", "ওষুধ",
    "help", "support", "assistance",
    "खाना", "पानी", "दवाई", "मदद", "सहायता",
    "அன்னம்", "தண்ணீர்", "உதவி", "மருத்துவ உதவி",
    "ఆహారం", "నీరు", "సహాయం",
    "ಆಹಾರ", "ನೀರು", "ಸಹಾಯ",
]

# STATUS/EVENT keywords that constitute meaningful content even without action/target
STATUS_KEYWORDS = [
    "communication link", "comm link", "radio link", "network", "signal",
    "still active", "operational", "connected", "disconnected",
    "link is active", "link is down", "comms up", "comms down",
    "building collapsed", "collapsed", "structure failed", "roof fallen",
]

# NUMBER WORD MAPPING (English + Indian languages)
NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    # Gujarati
    "એક": 1, "બે": 2, "ત્રણ": 3, "ચાર": 4, "પાંચ": 5,
    # Malayalam
    "ഒന്ന്": 1, "രണ്ട്": 2, "മൂന്ന്": 3, "നാല്": 4, "അഞ്ച്": 5,
    # Odia
    "ଏକ": 1, "ଦୁଇ": 2, "ତିନି": 3, "ଚାରି": 4, "ପାଞ୍ଚ": 5,
    # Bengali
    "এক": 1, "দুই": 2, "তিন": 3, "চার": 4, "পাঁচ": 5,
    # Hindi/Marathi
    "एक": 1, "दो": 2, "दोन": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाच": 5, "पाँच": 5,
    "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
    # Tamil
    "ஒன்று": 1, "இரண்டு": 2, "மூன்று": 3, "நான்கு": 4, "ஐந்து": 5,
    # Telugu
    "ఒకటి": 1, "రెండు": 2, "మూడు": 3, "నాలుగు": 4, "ఐదు": 5,
    # Kannada
    "ಒಂದು": 1, "ಎರಡು": 2, "ಮೂರು": 3, "ನಾಲ್ಕು": 4, "ಐದు": 5,
}

# Patterns that indicate a number is a QUANTITY (precedes people/casualty nouns)
_PEOPLE_QTY_RE = re.compile(
    r'\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|'
    r'ek|do|teen|char|paanch|'  # Romanised Hindi
    r'एक|दो|दोन|तीन|चार|पांच|पाच|पाँच)\s+'
    r'(?:people|persons|villager|villagers|casualt|victim|victims|'
    r'team|teams|member|members|soldier|soldiers|patient|patients|'
    r'men|women|man|woman|child|children|'
    r'लोग|लोगो|व्यक्ति|व्यक्तियों|பேர்|మంది)',
    re.IGNORECASE | re.UNICODE
)

# Proper-noun location patterns (original case preserved)
_PROPER_LOC_PATTERNS = [
    # Pattern 0 (highest priority): Hindi/Indic postposition — capture text BEFORE के पास / की तरफ
    re.compile(r'(?:(?:एक|दो|तीन|चार|पांच|पाच|पाँच)\s+लोग\s+)?([\u0900-\u097Fa-zA-Z]{2,}(?:\s+[\u0900-\u097Fa-zA-Z]+){0,3})\s+(?:के पास|की तरफ)'),
    # Pattern 1: "to/at/in/near/toward/towards SomePlace" — English only
    re.compile(r'(?i:\b(?:to|at|in|near|around|toward|towards|from)\s+(?:the\s+)?)([a-zA-Z0-9]{2,}(?:\s+[a-zA-Z0-9]+){0,3})\b'),
    # Pattern 2: "SomePlace area/zone/control …" — first word must be TitleCase
    re.compile(r'\b([A-Z][a-zA-Z]{2,}(?:\s+[a-zA-Z]+){0,2})\s+(?i:area|zone|region|district|city|town|village|camp|post|station|control|road|northern|southern)\b'),
    # Pattern 3: Sentence-start proper noun: "Nagpur control," or "Hubbli base,"
    re.compile(r'^([A-Z][a-z]{2,}(?:\s+[a-z]+){0,2})\s*(?i:control|base|hq|post|command)[\s,]'),
]

_LOCATION_STOPWORDS = {
    "Send", "The", "There", "People", "Everyone", "They", "He", "She",
    "It", "We", "I", "You", "This", "That", "All", "Some", "Many",
    "Please", "Now", "Here", "Fire", "Three", "Five",
    "Alpha", "Bravo", "Charlie", "Delta", "Team", "Group",
    "Rescue", "Medical", "Police", "Army", "Anyone",
    "immediately", "now", "right", "out", "and", "but", "so", "because",
    # Hindi stopwords — prevent fragments like "फंसे हुए" from being locations
    "फंसे", "हुए", "हैं", "हो", "को", "की", "और", "एक", "दो", "तीन",
    "तुरंत", "में", "का", "के", "कार",
}


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _match_table(text_lower: str, table: list) -> Optional[Tuple]:
    """Return (enum_value, matched_phrase) or None.  First match wins."""
    for enum_val, phrases in table:
        for phrase in phrases:
            if phrase.isascii():
                if re.search(rf'\b{re.escape(phrase.lower())}\b', text_lower):
                    return enum_val, phrase
            else:
                if phrase.lower() in text_lower:
                    return enum_val, phrase
    return None

def _match_all_table(text_lower: str, table: list) -> List[Tuple]:
    results = []
    for enum_val, phrases in table:
        for phrase in phrases:
            if phrase.isascii():
                if re.search(rf'\b{re.escape(phrase.lower())}\b', text_lower):
                    results.append((enum_val, phrase))
                    break
            else:
                if phrase.lower() in text_lower:
                    results.append((enum_val, phrase))
                    break
    return results

def _match_all_conditions(text_lower: str) -> List[Tuple]:
    """Return ALL matching condition entries (for multi-condition sentences)."""
    results = []
    for enum_val, phrases in CONDITION_MAP:
        for phrase in phrases:
            if phrase.isascii():
                if re.search(rf'\b{re.escape(phrase.lower())}\b', text_lower):
                    results.append((enum_val, phrase))
                    break
            else:
                if phrase.lower() in text_lower:
                    results.append((enum_val, phrase))
                    break
    return results

def _detect_quantity(text_lower: str, text_original: str) -> Optional[int]:
    """Extract meaningful quantity, skipping callsign/sector numbers."""
    # Scrub callsign numbers from the quantity search space
    scrubbed = _scrub_callsign_numbers(text_lower)

    # Priority 1: "N people / N victims / N teams …"
    m = _PEOPLE_QTY_RE.search(scrubbed)
    if m:
        raw = m.group(1)
        if raw.isdigit():
            return int(raw)
        return NUMBER_WORDS.get(raw.lower(), 1)

    # Priority 2: Indic/Unicode word numbers (substring match, no word boundary needed)
    for word, val in NUMBER_WORDS.items():
        if not word.isascii():
            if word in text_original:
                return val

    # Priority 3: English word numbers with word boundary
    for word, val in NUMBER_WORDS.items():
        if word.isascii() and word not in ("one", "two", "three", "four", "five",
                                            "six", "seven", "eight", "nine", "ten"):
            continue  # skip zero, handled below
        if word.isascii():
            if re.search(rf'\b{re.escape(word)}\b', scrubbed, re.IGNORECASE):
                return val

    # Priority 4: first standalone digit not in scrubbed-out callsign/sector
    digits = re.findall(r'\b(\d+)\b', scrubbed)
    if digits:
        return int(digits[0])

    return None

def _detect_proper_location(text: str) -> Optional[str]:
    """Try to extract an unknown proper-noun location from text (preserving original case)."""
    stop_lower = {s.lower() for s in _LOCATION_STOPWORDS}
    for pattern in _PROPER_LOC_PATTERNS:
        m = pattern.search(text)
        if m:
            candidate = m.group(1).strip()
            # Remove trailing common words if captured
            candidate = re.sub(r'\s+(control|base|hq|command|post)$', '', candidate, flags=re.IGNORECASE).strip()
            
            # strip trailing stopwords
            words = candidate.split()
            while words and words[-1].lower() in stop_lower:
                words.pop()
            if not words:
                continue
            
            candidate = " ".join(words)
            if candidate.split()[0].lower() not in stop_lower and len(candidate) >= 3:
                return candidate
    return None

def _detect_hazard(text_lower: str) -> Optional[str]:
    found = []
    for kw in HAZARD_KEYWORDS:
        kl = kw.lower()
        if kl in text_lower:
            # Avoid double-counting "fire" when "fire team/brigade" is in text
            if kl == "fire" and any(x in text_lower for x in ["fire team", "fire brigade", "fire fighter"]):
                continue
            found.append(kw)
    # Deduplicate
    seen = set()
    deduped = []
    for f in found:
        if f.lower() not in seen:
            seen.add(f.lower())
            deduped.append(f)
    return ", ".join(deduped) if deduped else None

def _detect_resource(text_lower: str) -> Optional[str]:
    found = [kw for kw in RESOURCE_KEYWORDS if kw.lower() in text_lower]
    return ", ".join(dict.fromkeys(found)) if found else None

def _has_status_content(text_lower: str) -> bool:
    """Returns True if the text contains meaningful status/event content."""
    return any(kw in text_lower for kw in STATUS_KEYWORDS)

def _detect_status(text_lower: str) -> Optional[str]:
    found = [kw for kw in STATUS_KEYWORDS if kw in text_lower]
    return ", ".join(dict.fromkeys(found)) if found else None

def _meaningful_field_count(msg: SemanticMessage) -> int:
    """Count how many non-trivial semantic fields were extracted."""
    count = 0
    if msg.action.code != 0: count += 1
    if msg.target.code != 0 or msg.location_text: count += 1
    if msg.entity.code != 0: count += 1
    if msg.urgency.code != 0: count += 1
    if msg.condition.code != 0: count += 1
    if msg.emotion.code != 0: count += 1
    if msg.quantity.code != 0: count += 1
    if msg.hazard_text: count += 1
    if msg.resource_text: count += 1
    if msg.extra_fields: count += len(msg.extra_fields)
    return count


# ─────────────────────────────────────────────
#  CORE PARSE LOGIC
# ─────────────────────────────────────────────

def _parse_core(text: str, language: str = "en") -> SemanticMessage:
    """
    Language-agnostic hybrid parsing (English-as-median: every keyword maps to
    the same canonical enum regardless of the source language).
    Extracts ALL applicable semantic fields from a sentence.
    `language` records the source language on the message for downstream
    consumers (hybrid TinyML, diagnostics); keyword matching itself uses the
    unified multilingual codebook so all 10 languages parse identically.
    """
    text_lower = text.lower()
    msg = SemanticMessage()
    msg.source_language = language
    matched = []

    # ── ACTION ──────────────────────────────
    result = _match_table(text_lower, ACTION_MAP)
    if result:
        ev, phrase = result
        msg.action = SemanticField("ACTION", ev.name, ev.value, phrase)
        matched.append("ACTION")

    # ── ENTITY ──────────────────────────────
    # Guard: don't let a fire-related action mask entity detection
    all_entities = _match_all_table(text_lower, ENTITY_MAP)
    valid_entities = []
    for ev, phrase in all_entities:
        if ev == Entity.FIRE:
            continue # FIRE is never an entity, only a hazard/event. (FIRE_TEAM handles team)
        valid_entities.append((ev, phrase))
        
    if valid_entities:
        ev, phrase = valid_entities[0]
        msg.entity = SemanticField("ENTITY", ev.name, ev.value, phrase)
        matched.append("ENTITY")
        for ev2, phrase2 in valid_entities[1:]:
            msg.extra_fields.append(SemanticField("RESOURCE_REQUIRED", ev2.name, ev2.value, phrase2))

    # ── TARGET (proper locations first) ──────
    proper_loc = _detect_proper_location(text)
    if proper_loc:
        msg.target = SemanticField(
            "TARGET", Target.PROPER_LOCATION.name, Target.PROPER_LOCATION.value,
            proper_loc, "PROPER_NOUN", 0.85
        )
        msg.location_text = proper_loc
        matched.append("TARGET")
        matched.append("LOCATION")
    else:
        result = _match_table(text_lower, TARGET_MAP)
        if result:
            ev, phrase = result
            msg.target = SemanticField("TARGET", ev.name, ev.value, phrase)
            matched.append("TARGET")

    # ── URGENCY ─────────────────────────────
    result = _match_table(text_lower, URGENCY_MAP)
    if result:
        ev, phrase = result
        msg.urgency = SemanticField("URGENCY", ev.name, ev.value, phrase)
        matched.append("URGENCY")

    # ── CONDITION (extract ALL matching) ─────
    all_conditions = _match_all_conditions(text_lower)
    if all_conditions:
        # Primary condition stored in msg.condition
        ev, phrase = all_conditions[0]
        msg.condition = SemanticField("CONDITION", ev.name, ev.value, phrase)
        matched.append("CONDITION")
        # Additional conditions stored as extra_fields
        for ev2, phrase2 in all_conditions[1:]:
            msg.extra_fields.append(
                SemanticField("CONDITION_DETAIL", ev2.name, ev2.value, phrase2)
            )
            matched.append("CONDITION_DETAIL")

    # ── EMOTION ─────────────────────────────
    result = _match_table(text_lower, EMOTION_MAP)
    if result:
        ev, phrase = result
        msg.emotion = SemanticField("EMOTION", ev.name, ev.value, phrase)
        matched.append("EMOTION")

    # ── IMPLICIT URGENCY INFERENCE ───────────
    if msg.urgency.code == 0:
        severe_conditions = {Condition.TRAPPED.value, Condition.UNCONSCIOUS.value, Condition.CRITICAL.value}
        severe_emotions   = {Emotion.PANIC.value, Emotion.DISTRESS.value, Emotion.FEAR.value}
        if msg.condition.code in severe_conditions or msg.emotion.code in severe_emotions:
            msg.urgency = SemanticField("URGENCY", Urgency.HIGH.name, Urgency.HIGH.value, "inferred-high")
            matched.append("URGENCY")

    # ── QUANTITY ────────────────────────────
    qty = _detect_quantity(text_lower, text)
    if qty is not None and qty > 0:
        msg.quantity = SemanticField("QUANTITY", qty, qty, str(qty))
        matched.append("QUANTITY")
    elif msg.action.code == Action.SEND_TEAM.value and qty is None:
        msg.quantity = SemanticField("QUANTITY", 1, 1, "implied one")
        matched.append("QUANTITY")

    # ── CALLSIGN DETECTION ──────────────────
    callsign_m = _CALLSIGN_RE.search(text)
    if callsign_m:
        cs_text = callsign_m.group(0)
        # Only add as extra_field if it looks like an identifier (not sector/zone)
        first_word = cs_text.split()[0].lower()
        if first_word not in ("sector", "zone", "block", "phase", "route", "road", "highway", "nh", "sh", "grid"):
            msg.extra_fields.append(SemanticField("CALLSIGN", cs_text, 0, cs_text, "TEXT", 0.9))
            matched.append("CALLSIGN")

    # ── DIRECTION ───────────────────────────
    for dir_kw in ["north", "south", "east", "west"]:
        if re.search(rf'\b{dir_kw}\b', text_lower):
            msg.extra_fields.append(SemanticField("DIRECTION", dir_kw.upper(), 0, dir_kw, "TEXT", 0.9))
            matched.append("DIRECTION")

    # ── HAZARD ──────────────────────────────
    hazard = _detect_hazard(text_lower)
    if hazard:
        msg.hazard_text = hazard
        matched.append("HAZARD")

    # ── RESOURCE ────────────────────────────
    resource = _detect_resource(text_lower)
    if resource:
        msg.resource_text = resource
        matched.append("RESOURCE")

    # ── STATUS ──────────────────────────────
    status = _detect_status(text_lower)
    if status:
        msg.status_text = status
        matched.append("STATUS")

    msg.matched_fields = matched
    return msg


# ─────────────────────────────────────────────
#  PUBLIC API
# ─────────────────────────────────────────────

def parse_english(text: str) -> SemanticMessage:
    return _parse_core(text)

def parse_hindi(text: str) -> SemanticMessage:
    return _parse_core(text, "hi")

def parse(text: str, language: str) -> SemanticMessage:
    """Parse text into a SemanticMessage using Hybrid Rule + TinyML parsing."""
    try:
        import hybrid_engine
        return hybrid_engine.parse(text, language)
    except Exception as e:
        # Graceful fallback to pure rule-based parse if TinyML fails to load
        msg = _parse_core(text, language)
        failed = []
        if msg.action.code == 0:
            failed.append("ACTION")
        if msg.target.code == 0 and not msg.location_text:
            failed.append("TARGET")
        if msg.entity.code == 0 and msg.action.code == Action.SEND_TEAM.value:
            failed.append("ENTITY")
        msg.failed_fields = failed

        meaningful = _meaningful_field_count(msg)
        has_status = _has_status_content(text.lower())
        if meaningful < 2 and not has_status:
            reason = f"Insufficient semantic content. Recognised fields: {', '.join(msg.matched_fields) or 'none'}"
            return SemanticMessage(
                fallback_text=text,
                fallback_reason=reason,
                matched_fields=msg.matched_fields,
                failed_fields=failed,
            )
        return msg
