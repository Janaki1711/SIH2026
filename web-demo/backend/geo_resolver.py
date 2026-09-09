"""
geo_resolver.py — Local Geographic Entity Resolver

Provides offline geographic entity resolution using phonetic matching (Soundex),
Levenshtein distance, and a local landmark database with GeoIDs.
"""

import re
from typing import Dict, List, Optional, Tuple
from semantic_codebook import GeoID

class LocationEntity:
    def __init__(self, canonical_name: str, geo_id: int, confidence: float = 1.0, matched_token: str = ""):
        self.canonical_name = canonical_name
        self.geo_id = geo_id
        self.confidence = confidence
        self.matched_token = matched_token

    def to_dict(self) -> Dict:
        return {
            "canonical_name": self.canonical_name,
            "geo_id": f"0x{self.geo_id:04X}",
            "confidence": round(self.confidence, 3),
            "matched_token": self.matched_token,
        }

    def __repr__(self):
        return f"LocationEntity({self.canonical_name}, 0x{self.geo_id:04X}, conf={self.confidence:.2f})"


def compute_soundex(word: str) -> str:
    """Compute Soundex code for Romanized words."""
    clean = re.sub(r'[^A-Za-z]', '', word).upper()
    if not clean:
        return ""
    first = clean[0]
    mapping = {
        'B': '1', 'F': '1', 'P': '1', 'V': '1',
        'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
        'D': '3', 'T': '3',
        'L': '4',
        'M': '5', 'N': '5',
        'R': '6'
    }
    code = [first]
    prev = mapping.get(first, '0')
    for ch in clean[1:]:
        curr = mapping.get(ch, '0')
        if curr != '0' and curr != prev:
            code.append(curr)
        prev = curr
        if len(code) == 4:
            break
    while len(code) < 4:
        code.append('0')
    return "".join(code)


def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if not s2:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def similarity_ratio(s1: str, s2: str) -> float:
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    dist = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1.0 - (dist / max_len)


class GeoResolver:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.landmarks: List[Dict] = []
        self._initialize_default_landmarks()

    def _initialize_default_landmarks(self):
        self.register_landmark("Tolankere", GeoID.TOLANKERE, [
            "tolankere", "tholankere", "tolan care", "tolan care lake", "tolankere lake", "tolankere tank",
            "तोलनकेरे", "தோலன்கெரே", "తోలంకెరె", "ತೊಳನಕೆರೆ",
            "તોલનકેરે", "തോളങ്കരെ", "ତୋଲାଙ୍କେରେ", "তোলনকেরে"
        ])
        self.register_landmark("Hubbli", GeoID.HUBBLI, [
            "hubbli", "hubli", "hübli", "hubballi", "hubly",
            "हब्बली", "हुबली", "ஹூப்ளி", "ஹுப்பள்ளி", "హుబ్లి", "హుబ్బళ్ళి", "ಹುಬ್ಬಳ್ಳಿ",
            "હબ્બલી", "ഹുബ്ലി", "ହୁବ୍ଲି", "হুবলি"
        ])
        self.register_landmark("Base Camp", GeoID.BASE, [
            "base camp", "base", "hq", "headquarters", "command base",
            "बेस", "आधार", "मुख्यालय", "બેઝ", "முகாம்", "బేస్", "ಬೇಸ್", "ബേസ്", "ବେସ୍", "বেস"
        ])
        self.register_landmark("Sector 1", GeoID.SECTOR_1, [
            "sector 1", "sector one", "सेक्टर 1", "सेक्टर एक", "સેક્ટર 1", "செக்டர் 1",
            "సెక్టార్ 1", "సెక్టర్ 1", "ಸೆಕ್ಟರ್ 1", "സെക്ടർ 1", "ସେକ୍ଟର 1", "সেক্টর 1", "zone 1"
        ])
        self.register_landmark("Sector 2", GeoID.SECTOR_2, [
            "sector 2", "sector two", "सेक्टर 2", "सेक्टर दो", "સેક્ટર 2", "செக்டர் 2",
            "సెక్టార్ 2", "సెక్టర్ 2", "ಸೆಕ್ಟರ್ 2", "സെക്ടർ 2", "ସେକ୍ଟର 2", "সেক্টর 2", "zone 2"
        ])
        self.register_landmark("Sector 3", GeoID.SECTOR_3, [
            "sector 3", "sector three", "सेक्टर 3", "सेक्टर तीन", "સેક્ટર 3", "செக்டர் 3",
            "సెక్టార్ 3", "సెక్టర్ 3", "ಸೆಕ್ಟರ್ 3", "സെക്ടർ 3", "ସେକ୍ଟର 3", "সেক্টর 3", "zone 3"
        ])
        self.register_landmark("Sector 4", GeoID.SECTOR_4, [
            "sector 4", "sector four", "सेक्टर 4", "सेक्टर चार", "સેક્ટર 4", "செக்டர் 4",
            "సెక్టార్ 4", "సెక్టర్ 4", "ಸೆಕ್ಟರ್ 4", "സെക്ടർ 4", "ସେକ୍ଟର 4", "সেক্টর 4", "zone 4"
        ])
        self.register_landmark("Sector 5", GeoID.SECTOR_5, [
            "sector 5", "sector five", "सेक्टर 5", "सेक्टर पांच", "સેક્ટર 5", "செக்டர் 5",
            "సెక్టార్ 5", "సెక్టర్ 5", "ಸೆಕ್ಟರ್ 5", "സെക്ടർ 5", "ସେକ୍ଟର 5", "সেক্টর 5", "zone 5"
        ])
        self.register_landmark("Bridge", GeoID.BRIDGE, [
            "old bridge", "bridge", "railway bridge", "river bridge",
            "पुल", "सेतु", "पूल", "પુલ", "பாலம்", "వంతెన", "ಸೇತುವೆ", "പാലം", "ପୋଲ", "পোল", "সেতু"
        ])
        self.register_landmark("Hospital", GeoID.HOSPITAL, [
            "hospital", "clinic", "district hospital", "general hospital",
            "अस्पताल", "हॉस्पिटल", "रुग्णालय", "હોસ્પિટલ", "દવાખાનું", "மருத்துவமனை",
            "ஆஸ்பத்திரி", "ఆసుపత్రి", "ದವಾಖಾನೆ", "ಆಸ್ಪತ್ರೆ", "ആശുപത്രി", "ଡାକ୍ତରଖାନା", "হাসপাতাল"
        ])
        self.register_landmark("School", GeoID.SCHOOL, [
            "school", "college", "campus",
            "स्कूल", "विद्यालय", "शाळा", "શાળા", "பள்ளி", "பாடசாலை", "పాఠశాల", "ಶಾಲೆ", "സ്കൂൾ", "ବିଦ୍ୟାଳୟ", "স্কুল"
        ])

    def register_landmark(self, canonical_name: str, geo_id: int, aliases: List[str]):
        norm_canonical = self._normalize(canonical_name)
        norm_aliases = [norm_canonical]
        phonetic_aliases = []
        for alias in aliases:
            na = self._normalize(alias)
            if na:
                norm_aliases.append(na)
                snd = compute_soundex(na)
                if snd:
                    phonetic_aliases.append(snd)
        self.landmarks.append({
            "canonical_name": canonical_name,
            "geo_id": geo_id,
            "aliases": norm_aliases,
            "phonetic_aliases": phonetic_aliases,
        })

    def _normalize(self, text: str) -> str:
        # Lowercase, retain alphanumeric and non-ASCII Indic characters, normalize spaces
        cleaned = re.sub(r'[^\w\s\u0900-\u0D7F]', ' ', text.lower())
        return " ".join(cleaned.split())

    def resolve_location(self, text: str) -> LocationEntity:
        if not text:
            return LocationEntity("", GeoID.UNKNOWN, 0.0)

        norm_text = self._normalize(text)
        best_match = LocationEntity("", GeoID.UNKNOWN, 0.0)

        # 1. Exact / Substring match
        for lm in self.landmarks:
            for alias in lm["aliases"]:
                if not alias:
                    continue
                if alias in norm_text:
                    conf = 0.98
                    if conf > best_match.confidence:
                        best_match = LocationEntity(lm["canonical_name"], lm["geo_id"], conf, alias)

        if best_match.confidence >= 0.95:
            return best_match

        # 2. Sliding window n-gram extraction for phonetic & approximate matching
        tokens = norm_text.split()
        n_tokens = len(tokens)
        for n in range(1, min(4, n_tokens + 1)):
            for start in range(n_tokens - n + 1):
                span = " ".join(tokens[start:start + n])
                span_soundex = compute_soundex(span)

                for lm in self.landmarks:
                    for a_idx, alias in enumerate(lm["aliases"]):
                        # Levenshtein ratio
                        sim = similarity_ratio(span, alias)
                        if sim >= 0.75 and sim > best_match.confidence:
                            best_match = LocationEntity(lm["canonical_name"], lm["geo_id"], sim * 0.95, span)

                        # Soundex phonetic match
                        if a_idx < len(lm["phonetic_aliases"]) and span_soundex:
                            if span_soundex == lm["phonetic_aliases"][a_idx]:
                                phon_conf = 0.88
                                if phon_conf > best_match.confidence:
                                    best_match = LocationEntity(lm["canonical_name"], lm["geo_id"], phon_conf, span)

        return best_match


def resolve_location(text: str) -> LocationEntity:
    """Convenience functional interface."""
    return GeoResolver.get_instance().resolve_location(text)
