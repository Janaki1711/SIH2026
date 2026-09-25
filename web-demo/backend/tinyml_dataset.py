# tinyml_dataset.py
"""
iTantra M3 — TinyML Dataset Generator
Generates realistic, contextual emergency & tactical communication examples
for training the lightweight Semantic Role Classifier.

Roles:
  0: CALLSIGN    (e.g., 'Alpha 12', 'Bravo 4', 'Unit 7', 'Delta 1', 'Charlie 9')
  1: LOCATION    (e.g., 'old railway bridge', 'Green Valley Hospital', 'Xyzgarh', 'Sector 4', 'Nagpur', 'Hubbli', 'river', 'नदी', 'ஹூப்ளி')
  2: QUANTITY    (e.g., 'three', 'two', 'five', '5', '12', 'पाँच', 'இரண்டு', 'seven', 'ten')
  3: RESOURCE    (e.g., 'ambulance', 'medical team', 'help', 'oxygen cylinders', 'medicines', 'relief packets', 'support', 'மருத்துவ உதவி')
  4: HAZARD      (e.g., 'unsafe', 'dangerous', 'building collapsed', 'fire', 'flood', 'landslide', 'toxic gas', 'தீ விபத்து', 'बाढ़')
  5: STATUS      (e.g., 'signal is weak', 'communication link is active', 'link is down', 'comms operational', 'network active')
  6: EMOTION     (e.g., 'terrified', 'panicking', 'scared', 'distress', 'frightened', 'fear', 'घबराए हुए', 'பீதி')
  7: CONDITION   (e.g., 'injured', 'unconscious', 'trapped', 'missing', 'critical', 'फंसे हुए', 'காயமடைந்தவர்கள்')
  8: ACTION      (e.g., 'send', 'moving', 'evacuate', 'requesting', 'search', 'deploy', 'भेजें', 'அனுப்புங்கள்')
  9: DIRECTION   (e.g., 'east', 'west', 'north', 'south', 'northeast', 'southwest', 'पूर्व', 'पश्चिम')
"""

import random
from typing import List, Dict, Tuple

ROLES = [
    "CALLSIGN",
    "LOCATION",
    "QUANTITY",
    "RESOURCE",
    "HAZARD",
    "STATUS",
    "EMOTION",
    "CONDITION",
    "ACTION",
    "DIRECTION",
]
ROLE2ID = {r: i for i, r in enumerate(ROLES)}
ID2ROLE = {i: r for i, r in enumerate(ROLES)}

# --- Vocabulary components for procedural contextual generator ---

CALLSIGN_NAMES_TRAIN = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hawk", "Eagle", "Falcon", "Tiger", "Panther", "Sierra", "Tango", "Victor", "Unit", "Squad", "Team"]
CALLSIGN_NAMES_TEST = ["Zulu", "Kestrel", "Osprey", "Viper", "Cobra", "Omega", "Phantom", "Spectre", "Titan", "Nomad", "Centurion", "Ronin"]

CALLSIGN_NUMS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "15", "21", "42", "77", "99"]

LOCATIONS_TRAIN = [
    "Hubbli", "Tolankere", "Nagpur", "Sector 1", "Sector 2", "Sector 3", "Sector 4", "Sector 5",
    "Green Valley Hospital", "old railway bridge", "Central Base", "North Post", "City School",
    "district warehouse", "Highway 48", "Sector 12", "civil hospital", "community clinic",
    "village near the river", "old bridge", "bridge", "hospital", "school", "camp",
    "Chandrapur", "Bhadravati", "Kalyan gate", "Southern ridge", "Sector 9", "base camp"
]
LOCATIONS_TEST = [
    "Xyzgarh", "old railway bridge", "Green Valley Hospital", "Sector 47", "Riverbank Post",
    "Devgarh", "Kopargaon", "Sitapur", "Rampur", "Zircon Valley", "Blue Ridge Road",
    "Hilltop Clinic", "Eastern crossing", "Sundar Nagar", "Palghat", "Anakapalli"
]

LOCATIONS_HINDI_TRAIN = ["नदी", "पुल", "अस्पताल", "स्कूल", "बेस", "सेक्टर चार", "हब्बली", "नागपुर", "तोलनकेरे", "कैंप"]
LOCATIONS_HINDI_TEST = ["देवगढ़", "रामपुर", "सीतापुर", "नदी", "पुराना रेलवे पुल", "ग्रीन वैली हॉस्पिटल"]

LOCATIONS_TAMIL_TRAIN = ["ஹூப்ளி", "தோலன்கெரே", "பாலம்", "மருத்துவமனை", "பள்ளி", "நான்காம் பகுதி", "நதி"]
LOCATIONS_TAMIL_TEST = ["தேவ்கர்", "பழைய பாலம்", "ராம்பூர்"]

QUANTITY_WORDS_TRAIN = [
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "12", "15", "20",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "एक", "दो", "तीन", "चार", "पांच", "पाँच", "छह", "सात", "आठ", "नौ", "दस",
    "ஒன்று", "இரண்டு", "மூன்று", "நான்கு", "ஐந்து",
    "ఒకటి", "రెండు", "మూడు", "నాలుగు", "ఐదు",
    "ಒಂದು", "ಎರಡು", "ಮೂರು", "ನಾಲ್ಕು", "ಐದು"
]
QUANTITY_WORDS_TEST = [
    "3", "5", "7", "11", "25", "two", "three", "five", "seven", "twelve",
    "पाँच", "दो", "तीन", "இரண்டு", "மூன்று", "ஐந்து"
]

RESOURCES_TRAIN = [
    "ambulance", "medical team", "rescue team", "help", "support", "assistance",
    "fire brigade", "fire truck", "oxygen cylinders", "medicines", "food packets",
    "drinking water", "blankets", "rescue boats", "emergency generator", "blood units",
    "stretcher", "first aid kit", "relief supplies", "police team", "helicopter"
]
RESOURCES_TEST = [
    "ambulance", "medical team", "help", "trauma kit", "inflatable boat",
    "blood units", "clean water supplies", "rescue harness", "mobile ICU",
    "மருத்துவ உதவி", "मदद", "चिकित्सा सहायता"
]

HAZARDS_TRAIN = [
    "unsafe", "dangerous", "fire", "flood", "building collapsed", "landslide",
    "gas leak", "chemical spill", "explosion", "toxic fumes", "structure failed",
    "roof fallen", "heavy flooding", "dense smoke", "high radiation", "live wire hazard",
    "roadblock", "debris blockage"
]
HAZARDS_TEST = [
    "unsafe", "dangerous", "building collapsed", "fire", "collapsed bridge",
    "dam breach", "toxic cloud", "seismic tremor", "தீ விபத்து", "आग", "बाढ़"
]

STATUSES_TRAIN = [
    "signal is weak", "communication link is active", "link is down", "comms operational",
    "link is connected", "network active", "radio link established", "power restored",
    "battery low", "signal strength high", "repeater offline", "data link functional"
]
STATUSES_TEST = [
    "signal is weak", "communication link is active", "signal is weak and noisy",
    "mesh link stable", "RF link disconnected", "telemetry online"
]

EMOTIONS_TRAIN = [
    "terrified", "panicking", "scared", "in distress", "frightened", "fear",
    "desperate", "hysterical", "distressed", "panicked", "calm", "relieved",
    "घबराए हुए", "डर के मारे", "पीड़ित", "பீதியடைந்தவர்கள்"
]
EMOTIONS_TEST = [
    "terrified", "scared", "panicking", "fearful", "severely distressed",
    "घबराए हुए", "பீதியடைந்த"
]

CONDITIONS_TRAIN = [
    "injured", "unconscious", "trapped", "missing", "critical", "bleeding",
    "severe fracture", "burn victims", "dehydrated", "hypothermia", "safe",
    "फंसे हुए", "घायल", "बेहोश", "लापता", "காயமடைந்தவர்கள்", "சிக்கியிருக்கிறார்கள்"
]
CONDITIONS_TEST = [
    "injured", "unconscious", "trapped", "missing", "multiple fractures",
    "फंसे हुए", "घायल", "காயமடைந்தவர்கள்"
]

DIRECTIONS = ["east", "west", "north", "south", "northeast", "northwest", "southeast", "southwest", "eastern", "western", "northern", "southern"]
ACTIONS = ["send", "dispatch", "deploy", "moving", "advance", "evacuate", "requesting", "search", "secure", "hold", "report"]


def generate_example(is_test: bool = False) -> Dict:
    """Generate a single contextual training or evaluation sample with a targeted span and surrounding context."""
    locs = LOCATIONS_TEST if is_test else LOCATIONS_TRAIN
    cs_names = CALLSIGN_NAMES_TEST if is_test else CALLSIGN_NAMES_TRAIN
    qtys = QUANTITY_WORDS_TEST if is_test else QUANTITY_WORDS_TRAIN
    res = RESOURCES_TEST if is_test else RESOURCES_TRAIN
    haz = HAZARDS_TEST if is_test else HAZARDS_TRAIN
    stat = STATUSES_TEST if is_test else STATUSES_TRAIN
    emo = EMOTIONS_TEST if is_test else EMOTIONS_TRAIN
    conds = CONDITIONS_TEST if is_test else CONDITIONS_TRAIN

    role = random.choice(ROLES)

    left_ctx = ""
    target_span = ""
    right_ctx = ""

    if role == "CALLSIGN":
        name = random.choice(cs_names)
        num = random.choice(CALLSIGN_NUMS)
        has_team = random.random() < 0.5
        target_span = f"{name} {num}"
        if has_team:
            prefix = random.choice(["Team", "Unit", "Squad", "Group", "Patrol"])
            template = random.choice([
                (f"{prefix} ", " is moving toward the waypoint."),
                (f"{prefix} ", f" is heading {random.choice(DIRECTIONS)}."),
                (f"Contact ", " immediately for status update."),
                (f"Deploy ", f" to {random.choice(locs)}."),
                (f"{prefix} ", " is requesting backup."),
                (f"Report from ", " indicates clear perimeter."),
                (f"This is ", f" proceeding to {random.choice(locs)}."),
            ])
            left_ctx, right_ctx = template
        else:
            template = random.choice([
                ("Radio check for ", " on frequency primary."),
                ("Moving with ", " through the valley."),
                ("Callsign ", " confirm your coordinates."),
                ("Direct ", f" to proceed {random.choice(DIRECTIONS)}."),
                ("", " has reached checkpoint bravo."),
            ])
            left_ctx, right_ctx = template

    elif role == "LOCATION":
        loc = random.choice(locs)
        target_span = loc
        template = random.choice([
            ("Send help to ", " immediately."),
            ("Moving east toward ", " right now."),
            ("Heavy damage reported at ", " after the incident."),
            ("Deploy rescue team to ", " as soon as possible."),
            ("People are trapped near ", "."),
            ("Proceeding from base to ", " with emergency supplies."),
            ("Fire has broken out behind ", "."),
            ("We have arrived at ", " and set up perimeter."),
            ("Evacuate all civilians from ", " immediately."),
            ("Establish checkpoint at ", "."),
        ])
        left_ctx, right_ctx = template

    elif role == "QUANTITY":
        q = random.choice(qtys)
        target_span = q
        noun = random.choice(["people", "villagers", "rescue workers", "civilians", "casualties", "patients", "victims", "soldiers", "persons"])
        template = random.choice([
            ("There are ", f" {noun} trapped under debris."),
            ("Send ", f" {noun} to the hospital immediately."),
            ("We found ", f" {noun} who are injured."),
            ("Approximately ", f" {noun} require medical evacuation."),
            ("Total count is ", f" {noun} unaccounted for."),
            ("", f" {noun} are injured and one is unconscious."),
            ("Deploy ", f" rescue teams right now."),
        ])
        left_ctx, right_ctx = template

    elif role == "RESOURCE":
        r = random.choice(res)
        target_span = r
        template = random.choice([
            ("We urgently need an ", " at the staging area."),
            ("Please send ", " to the old bridge immediately."),
            ("Requesting additional ", " support right now."),
            ("Dispatch ", f" to {random.choice(locs)}."),
            ("Supplying ", " for the evacuation camp."),
            ("Require emergency ", " and medical supplies."),
            ("We need an ", " and a medical team right now."),
        ])
        left_ctx, right_ctx = template

    elif role == "HAZARD":
        h = random.choice(haz)
        target_span = h
        template = random.choice([
            ("The area is ", " and the road is blocked."),
            ("Alert: ", " reported in the northern zone."),
            ("Caution advised because ", " has occurred near the road."),
            ("Threat assessment indicates ", " conditions."),
            ("Evacuate immediately due to ", " danger."),
            ("After the ", f", {random.choice(qtys)} people are missing."),
            ("The site is ", " but communication link is active."),
        ])
        left_ctx, right_ctx = template

    elif role == "STATUS":
        s = random.choice(stat)
        target_span = s
        template = random.choice([
            ("The area is dangerous, but the ", "."),
            ("Report: ", " at the forward observation post."),
            ("Although conditions are severe, ", "."),
            ("Notice: ", " across all units."),
            ("Update: ", " and telemetry is incoming."),
        ])
        left_ctx, right_ctx = template

    elif role == "EMOTION":
        e = random.choice(emo)
        target_span = e
        template = random.choice([
            ("Everyone is ", " after the building collapsed."),
            ("Civilians are ", " and crying for help."),
            ("The crowd is in deep ", " and seeking shelter."),
            ("People are ", " due to sudden flooding."),
            ("Situation tense, locals are ", "."),
        ])
        left_ctx, right_ctx = template

    elif role == "CONDITION":
        c = random.choice(conds)
        target_span = c
        template = random.choice([
            ("Two people are ", " and one is in critical care."),
            ("Villagers are ", " inside the collapsed structure."),
            ("Five victims confirmed ", " near the riverbank."),
            ("Patient is ", " and unresponsive."),
            ("All team members are ", " and accounted for."),
        ])
        left_ctx, right_ctx = template

    elif role == "ACTION":
        a = random.choice(ACTIONS)
        target_span = a
        template = random.choice([
            ("Please ", f" rescue teams to {random.choice(locs)}."),
            ("We are ", f" {random.choice(DIRECTIONS)} toward the waypoint."),
            ("Command order to ", " all personnel immediately."),
            ("Urgent request to ", " medical supplies."),
            ("Team will ", f" the perimeter at {random.choice(locs)}."),
        ])
        left_ctx, right_ctx = template

    elif role == "DIRECTION":
        d = random.choice(DIRECTIONS)
        target_span = d
        template = random.choice([
            ("Team is moving ", f" toward {random.choice(locs)}."),
            ("Evacuate heading ", " away from danger zone."),
            ("Advance ", " along the highway."),
            ("Wind blowing from the ", " bringing toxic smoke."),
            ("Patrol the ", " sector immediately."),
        ])
        left_ctx, right_ctx = template

    full_text = f"{left_ctx}{target_span}{right_ctx}".strip()
    return {
        "text": full_text,
        "span": target_span,
        "left_ctx": left_ctx.strip(),
        "right_ctx": right_ctx.strip(),
        "role": role,
        "role_id": ROLE2ID[role],
    }


def generate_curated_edge_cases() -> List[Dict]:
    """Add deterministic edge cases addressing the exact ambiguity problems."""
    return [
        # Callsign numbers vs Quantities
        {"text": "Team Alpha 12 is moving east toward the old railway bridge.", "span": "Alpha 12", "left_ctx": "Team", "right_ctx": "is moving east toward the old railway bridge.", "role": "CALLSIGN", "role_id": ROLE2ID["CALLSIGN"]},
        {"text": "Team Alpha 12 is moving east toward the old railway bridge.", "span": "east", "left_ctx": "Team Alpha 12 is moving", "right_ctx": "toward the old railway bridge.", "role": "DIRECTION", "role_id": ROLE2ID["DIRECTION"]},
        {"text": "Team Alpha 12 is moving east toward the old railway bridge.", "span": "old railway bridge", "left_ctx": "Team Alpha 12 is moving east toward the", "right_ctx": ".", "role": "LOCATION", "role_id": ROLE2ID["LOCATION"]},
        {"text": "Rescue team Alpha 7 is moving towards the northern road.", "span": "Alpha 7", "left_ctx": "Rescue team", "right_ctx": "is moving towards the northern road.", "role": "CALLSIGN", "role_id": ROLE2ID["CALLSIGN"]},
        {"text": "Rescue team Alpha 7 is moving towards the northern road.", "span": "northern road", "left_ctx": "Rescue team Alpha 7 is moving towards the", "right_ctx": ".", "role": "LOCATION", "role_id": ROLE2ID["LOCATION"]},
        {"text": "Unit Alpha 7 is requesting medical support.", "span": "Alpha 7", "left_ctx": "Unit", "right_ctx": "is requesting medical support.", "role": "CALLSIGN", "role_id": ROLE2ID["CALLSIGN"]},
        {"text": "Send help to Sector 4 immediately.", "span": "Sector 4", "left_ctx": "Send help to", "right_ctx": "immediately.", "role": "LOCATION", "role_id": ROLE2ID["LOCATION"]},
        {"text": "Sector 47 is unsafe.", "span": "Sector 47", "left_ctx": "", "right_ctx": "is unsafe.", "role": "LOCATION", "role_id": ROLE2ID["LOCATION"]},
        {"text": "Sector 47 is unsafe.", "span": "unsafe", "left_ctx": "Sector 47 is", "right_ctx": ".", "role": "HAZARD", "role_id": ROLE2ID["HAZARD"]},
        {"text": "Send three rescue workers to Green Valley Hospital immediately.", "span": "three", "left_ctx": "Send", "right_ctx": "rescue workers to Green Valley Hospital immediately.", "role": "QUANTITY", "role_id": ROLE2ID["QUANTITY"]},
        {"text": "Send three rescue workers to Green Valley Hospital immediately.", "span": "rescue workers", "left_ctx": "Send three", "right_ctx": "to Green Valley Hospital immediately.", "role": "RESOURCE", "role_id": ROLE2ID["RESOURCE"]},
        {"text": "Send three rescue workers to Green Valley Hospital immediately.", "span": "Green Valley Hospital", "left_ctx": "Send three rescue workers to", "right_ctx": "immediately.", "role": "LOCATION", "role_id": ROLE2ID["LOCATION"]},
        {"text": "Two people are injured and one is unconscious.", "span": "two", "left_ctx": "", "right_ctx": "people are injured and one is unconscious.", "role": "QUANTITY", "role_id": ROLE2ID["QUANTITY"]},
        {"text": "Two people are injured and one is unconscious.", "span": "injured", "left_ctx": "Two people are", "right_ctx": "and one is unconscious.", "role": "CONDITION", "role_id": ROLE2ID["CONDITION"]},
        {"text": "Two people are injured and one is unconscious.", "span": "unconscious", "left_ctx": "Two people are injured and one is", "right_ctx": ".", "role": "CONDITION", "role_id": ROLE2ID["CONDITION"]},
        {"text": "Everyone is terrified after the building collapsed near Nagpur.", "span": "terrified", "left_ctx": "Everyone is", "right_ctx": "after the building collapsed near Nagpur.", "role": "EMOTION", "role_id": ROLE2ID["EMOTION"]},
        {"text": "Everyone is terrified after the building collapsed near Nagpur.", "span": "building collapsed", "left_ctx": "Everyone is terrified after the", "right_ctx": "near Nagpur.", "role": "HAZARD", "role_id": ROLE2ID["HAZARD"]},
        {"text": "Everyone is terrified after the building collapsed near Nagpur.", "span": "Nagpur", "left_ctx": "Everyone is terrified after the building collapsed near", "right_ctx": ".", "role": "LOCATION", "role_id": ROLE2ID["LOCATION"]},
        {"text": "We need an ambulance and a medical team right now.", "span": "ambulance", "left_ctx": "We need an", "right_ctx": "and a medical team right now.", "role": "RESOURCE", "role_id": ROLE2ID["RESOURCE"]},
        {"text": "We need an ambulance and a medical team right now.", "span": "medical team", "left_ctx": "We need an ambulance and a", "right_ctx": "right now.", "role": "RESOURCE", "role_id": ROLE2ID["RESOURCE"]},
        {"text": "Send help to Xyzgarh immediately.", "span": "Xyzgarh", "left_ctx": "Send help to", "right_ctx": "immediately.", "role": "LOCATION", "role_id": ROLE2ID["LOCATION"]},
        {"text": "Send help to Xyzgarh immediately.", "span": "help", "left_ctx": "Send", "right_ctx": "to Xyzgarh immediately.", "role": "RESOURCE", "role_id": ROLE2ID["RESOURCE"]},
        {"text": "The area is dangerous, but the communication link is still active.", "span": "dangerous", "left_ctx": "The area is", "right_ctx": ", but the communication link is still active.", "role": "HAZARD", "role_id": ROLE2ID["HAZARD"]},
        {"text": "The area is dangerous, but the communication link is still active.", "span": "communication link is still active", "left_ctx": "The area is dangerous, but the", "right_ctx": ".", "role": "STATUS", "role_id": ROLE2ID["STATUS"]},
        {"text": "The area is dangerous and the signal is weak.", "span": "signal is weak", "left_ctx": "The area is dangerous and the", "right_ctx": ".", "role": "STATUS", "role_id": ROLE2ID["STATUS"]},
        {"text": "Seven people are trapped near the river.", "span": "seven", "left_ctx": "", "right_ctx": "people are trapped near the river.", "role": "QUANTITY", "role_id": ROLE2ID["QUANTITY"]},
        {"text": "Seven people are trapped near the river.", "span": "river", "left_ctx": "Seven people are trapped near the", "right_ctx": ".", "role": "LOCATION", "role_id": ROLE2ID["LOCATION"]},
        {"text": "Seven people are trapped near the river.", "span": "trapped", "left_ctx": "Seven people are", "right_ctx": "near the river.", "role": "CONDITION", "role_id": ROLE2ID["CONDITION"]},
        # Indic & Multilingual cases
        {"text": "पाँच लोग नदी के पास फंसे हुए हैं, तुरंत बचाव दल भेजें।", "span": "पाँच", "left_ctx": "", "right_ctx": "लोग नदी के पास फंसे हुए हैं, तुरंत बचाव दल भेजें।", "role": "QUANTITY", "role_id": ROLE2ID["QUANTITY"]},
        {"text": "पाँच लोग नदी के पास फंसे हुए हैं, तुरंत बचाव दल भेजें।", "span": "नदी", "left_ctx": "पाँच लोग", "right_ctx": "के पास फंसे हुए हैं, तुरंत बचाव दल भेजें।", "role": "LOCATION", "role_id": ROLE2ID["LOCATION"]},
        {"text": "पाँच लोग नदी के पास फंसे हुए हैं, तुरंत बचाव दल भेजें।", "span": "फंसे हुए", "left_ctx": "पाँच लोग नदी के पास", "right_ctx": "हैं, तुरंत बचाव दल भेजें।", "role": "CONDITION", "role_id": ROLE2ID["CONDITION"]},
        {"text": "पाँच लोग नदी के पास फंसे हुए हैं, तुरंत बचाव दल भेजें।", "span": "बचाव दल", "left_ctx": "पाँच लोग नदी के पास फंसे हुए हैं, तुरंत", "right_ctx": "भेजें।", "role": "RESOURCE", "role_id": ROLE2ID["RESOURCE"]},
        {"text": "தீ விபத்து ஏற்பட்டுள்ளது, இரண்டு பேர் காயமடைந்துள்ளனர், உடனடியாக மருத்துவ உதவியை அனுப்புங்கள்.", "span": "தீ விபத்து", "left_ctx": "", "right_ctx": "ஏற்பட்டுள்ளது, இரண்டு பேர் காயமடைந்துள்ளனர், உடனடியாக மருத்துவ உதவியை அனுப்புங்கள்.", "role": "HAZARD", "role_id": ROLE2ID["HAZARD"]},
        {"text": "தீ விபத்து ஏற்பட்டுள்ளது, இரண்டு பேர் காயமடைந்துள்ளனர், உடனடியாக மருத்துவ உதவியை அனுப்புங்கள்.", "span": "இரண்டு", "left_ctx": "தீ விபத்து ஏற்பட்டுள்ளது,", "right_ctx": "பேர் காயமடைந்துள்ளனர், உடனடியாக மருத்துவ உதவியை அனுப்புங்கள்.", "role": "QUANTITY", "role_id": ROLE2ID["QUANTITY"]},
        {"text": "தீ விபத்து ஏற்பட்டுள்ளது, இரண்டு பேர் காயமடைந்துள்ளனர், உடனடியாக மருத்துவ உதவியை அனுப்புங்கள்.", "span": "காயமடைந்துள்ளனர்", "left_ctx": "தீ விபத்து ஏற்பட்டுள்ளது, இரண்டு பேர்", "right_ctx": ", உடனடியாக மருத்துவ உதவியை அனுப்புங்கள்.", "role": "CONDITION", "role_id": ROLE2ID["CONDITION"]},
        {"text": "தீ விபத்து ஏற்பட்டுள்ளது, இரண்டு பேர் காயமடைந்துள்ளனர், உடனடியாக மருத்துவ உதவியை அனுப்புங்கள்.", "span": "மருத்துவ உதவி", "left_ctx": "தீ விபத்து ஏற்பட்டுள்ளது, இரண்டு பேர் காயமடைந்துள்ளனர், உடனடியாக", "right_ctx": "யை அனுப்புங்கள்.", "role": "RESOURCE", "role_id": ROLE2ID["RESOURCE"]},
    ]


def build_dataset(num_train: int = 1500, num_test: int = 400, seed: int = 42) -> Tuple[List[Dict], List[Dict]]:
    """Builds synthetic reproducible train and test datasets."""
    random.seed(seed)
    train_data = []
    for _ in range(num_train):
        train_data.append(generate_example(is_test=False))
    train_data.extend(generate_curated_edge_cases())

    test_data = []
    for _ in range(num_test):
        test_data.append(generate_example(is_test=True))
    test_data.extend(generate_curated_edge_cases())

    return train_data, test_data
