"""Build iTantra SIH 2026 deck as .pptx using ONLY the Python standard library.

.pptx = zip of OpenXML parts. No python-pptx needed (no network on this box).
Validates by re-parsing every XML part; visual check via soffice PDF export.
"""
import zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

OUT = "/home/janaki/SIH2026/iTantra_SIH2026.pptx"

# ---- theme ----
NAVY = "0B1E3A"       # slide background
CARD = "16294A"       # card fill
SAFFRON = "FF6B1A"    # accent
TEAL = "00C2A8"       # second accent
WHITE = "FFFFFF"
MUTED = "C9D4E3"
INK = "0B1E3A"

EMU = 914400
SW, SH = int(13.333 * EMU), int(7.5 * EMU)   # 16:9

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CP = "http://schemas.openxmlformats.org/package/2006/content-types"

_shape_id = [0]


def nid():
    _shape_id[0] += 1
    return _shape_id[0]


def tx_body(paras):
    """paras: list of dicts {runs:[(text,size,bold,color)], level, bullet, spaceAfter, align}"""
    out = ['<a:bodyPr wrap="square" lIns="91440" rIns="91440" tIns="45720" bIns="45720">'
           '<a:noAutofit/></a:bodyPr><a:lstStyle/>']
    for p in paras:
        lvl = p.get("level", 0)
        alg = f' alg="{p["align"]}"' if p.get("align") else ""
        mar = ' marL="0" indent="0"' if not p.get("bullet") else ""
        out.append(f'<a:p{alg}><a:pPr lvl="{lvl}"{mar}>')
        if p.get("bullet"):
            out.append('<a:buChar char="•"/><a:buSzPct val="100000"/>')
        else:
            out.append('<a:buNone/>')
        # NOTE: no a:lnSpc — LibreOffice Impress drops paragraphs carrying
        # line-spacing elements in this shape path. Default spacing is used.
        out.append('</a:pPr>')
        for text, size, bold, color in p["runs"]:
            b = ' b="1"' if bold else ""
            out.append(
                f'<a:r><a:rPr lang="en-US" sz="{size * 100}"{b} dirty="0">'
                f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
                f'<a:latin typeface="Calibri"/></a:rPr>'
                f'<a:t xml:space="preserve">{escape(text)}</a:t></a:r>'
            )
        out.append('</a:p>')
    return "".join(out)


def P_(runs, **kw):
    return {"runs": runs, **kw}


def T(text, size=16, bold=False, color=WHITE):
    return (text, size, bold, color)


def shape(x, y, w, h, paras, fill=None, line=None):
    i = nid()
    sp = (f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="s{i}"/>'
          f'<p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>'
          f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>'
          f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>')
    if fill:
        sp += f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
    else:
        sp += "<a:noFill/>"
    if line:
        sp += (f'<a:ln w="12700"><a:solidFill><a:srgbClr val="{line}"/>'
               f"</a:solidFill></a:ln>")
    else:
        sp += "<a:ln><a:noFill/></a:ln>"
    sp += "</p:spPr><p:txBody>" + tx_body(paras) + "</p:txBody></p:sp>"
    return sp


def bar(x, y, w, h, fill):
    """Solid accent bar (no text)."""
    i = nid()
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="b{i}"/>'
            f'<p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>'
            f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
            f"<a:ln><a:noFill/></a:ln></p:spPr>"
            f"<p:txBody><a:bodyPr/><a:lstStyle/>"
            f"<a:p><a:pPr><a:buNone/></a:pPr><a:endParaRPr/></a:p>"
            f"</p:txBody></p:sp>")


def header(kicker, title):
    I = EMU
    parts = [
        bar(int(0.5 * I), int(0.35 * I), int(0.6 * I), int(0.08 * I), SAFFRON),
        shape(int(0.5 * I), int(0.55 * I), int(12.33 * I), int(0.45 * I),
              [P_([T(kicker, 13, True, SAFFRON)])]),
        shape(int(0.5 * I), int(0.95 * I), int(12.33 * I), int(0.85 * I),
              [P_([T(title, 32, True, WHITE)])]),
        bar(int(0.5 * I), int(1.85 * I), int(12.33 * I), int(0.035 * I), "24344F"),
    ]
    return "".join(parts)


def footer(n):
    I = EMU
    return shape(int(0.5 * I), int(7.0 * I), int(12.33 * I), int(0.3 * I),
                 [P_([T(f"Team iTantra  •  SIH2026 / ISRO-01  •  {n} / 6", 10, False, MUTED)],
                     align="r")])


def bullets(items, size=15, gap=100):
    """items: list of (head, tail) or plain strings. Uses a literal bullet
    glyph in the run text (LibreOffice drops paragraphs carrying a:buChar)."""
    out = []
    for it in items:
        if isinstance(it, str):
            out.append(P_([T("•  " + it, size, False, WHITE)],
                          spaceAfter=gap))
        else:
            head, tail = it
            runs = [T("•  " + head + "   ", size, True, SAFFRON)]
            if tail:
                runs.append(T(tail, size, False, WHITE))
            out.append(P_(runs, spaceAfter=gap))
    return out


def slide_xml(shapes):
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<p:sld xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}"><p:cSld>'
        f'<p:bg><p:bgPr><a:solidFill><a:srgbClr val="{NAVY}"/>'
        "</a:solidFill></p:bgPr></p:bg>"
        f'<p:spTree><p:nvGrpSpPr><p:cNvPr id="0" name=""/>'
        "<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>"
        '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{SW}" cy="{SH}"/><a:chOff x="0" y="0"/>'
        f'<a:chExt cx="{SW}" cy="{SH}"/></a:xfrm></p:grpSpPr>'
        + shapes + "</p:spTree></p:cSld>"
        '<p:clrMapOvr><a:overrideClrMapping bg1="lt1" tx1="dk1" bg2="lt2" '
        'tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" '
        'accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" '
        'folHlink="folHlink"/></p:clrMapOvr></p:sld>')


I = EMU
COL_L = dict(x=int(0.5 * I), w=int(5.9 * I))
COL_R = dict(x=int(6.93 * I), w=int(5.9 * I))
TOP = int(2.1 * I)

# ================= SLIDE 1 — title =================
s1 = (
    bar(int(0.7 * I), int(1.1 * I), int(0.9 * I), int(0.1 * I), SAFFRON)
    + shape(int(0.7 * I), int(1.4 * I), int(11.9 * I), int(0.5 * I),
            [P_([T("SIH 2026  •  PROBLEM STATEMENT ISRO-01  •  TEAM iTANTRA",
                    14, True, SAFFRON)])])
    + shape(int(0.7 * I), int(1.95 * I), int(11.9 * I), int(1.4 * I),
            [P_([T("iTantra", 54, True, WHITE)])])
    + shape(int(0.7 * I), int(3.15 * I), int(11.9 * I), int(1.1 * I),
            [P_([T("Ultra-Low Bitrate Offline Multilingual Walkie-Talkie "
                    "& Tactical Emergency Mesh", 22, False, WHITE)])])
    + shape(int(0.7 * I), int(4.35 * I), int(11.9 * I), int(0.9 * I),
            [P_([T("Lightweight on-device STT + TTS for 10 Indian languages — "
                    "no towers, no internet, no cloud.  Speech in, voice out.",
                    15, False, MUTED)])])
    + shape(int(0.7 * I), int(5.5 * I), int(5.6 * I), int(1.1 * I),
            [P_([T("THEME  ", 12, True, SAFFRON),
                  T("Disaster Management & Tactical Emergency Comm.", 13, False, WHITE)])],
            fill=CARD, line="24344F")
    + shape(int(6.6 * I), int(5.5 * I), int(5.6 * I), int(1.1 * I),
            [P_([T("CATEGORY  ", 12, True, TEAL),
                  T("Software — TinyML / Edge AI / Wireless Mesh", 13, False, WHITE)])],
            fill=CARD, line="24344F")
    + footer(1)
)

# ================= SLIDE 2 — idea =================
def flow_step(x, y, w, h, label, fill):
    return shape(x, y, w, h, [P_([T(label, 11, True, WHITE)], align="ctr")],
                 fill=fill, line=None)


def flow_arrow(x, y, w, h):
    return shape(x, y, w, h, [P_([T("→", 16, True, SAFFRON)], align="ctr")])


def _flow_strip(y):
    steps = [("Speech", TEAL), ("VAD", "3A86FF"), ("STT", SAFFRON),
             ("UTF-8 Text", "2BA84A"), ("Mesh Tx", "8338EC"),
             ("TTS", "3A86FF"), ("Voice", TEAL)]
    bw, gap, h = int(1.5 * I), int(0.28 * I), int(0.72 * I)
    x = int(0.5 * I)
    parts = []
    for idx, (label, fill) in enumerate(steps):
        parts.append(flow_step(x, y, bw, h, label, fill))
        x += bw
        if idx < len(steps) - 1:
            parts.append(flow_arrow(x, y, gap, h))
            x += gap
    return "".join(parts)


s2 = (
    header("IDEA & INNOVATION",
           "iTantra — Send Meaning, Not Audio")
    + _flow_strip(int(1.95 * I))
    + shape(int(0.5 * I), int(2.85 * I), int(3.95 * I), int(2.35 * I),
            [P_([T("PROBLEM", 15, True, "6C3CE0")])]
            + [P_([T("•  " + t, 11, False, INK)]) for t in [
                "Voice audio too heavy for low-rate links.",
                "Text alerts exclude non-literate users.",
                "STT must fire on pauses, form sentences, stream instantly.",
                "Alerts must be voice: max-volume, non-interruptible.",
                "10 languages, offline, on low-power phones."]],
            fill="E9EFFA", line="6C3CE0")
    + shape(int(4.6 * I), int(2.85 * I), int(3.95 * I), int(2.35 * I),
            [P_([T("OUR SOLUTION", 14, True, TEAL)])]
            + [P_([T("•  " + t, 11, False, WHITE)]) for t in [
                "Silero VAD gate → PTT release → dual-engine STT (whisper/conformer).",
                "Speech → UTF-8 transcript: 42 B vs 48,000 B PCM ≈1,100× less data.",
                "Wi-Fi Direct / BT mesh; ChaCha20-Poly1305 + RS-FEC (K=8/M=4).",
                "Receiver TTS in own language; SOS siren override.",
                "PTT walkie-talkie / phone / SOS; 100% OSS, zero cloud."]],
            fill=CARD, line=TEAL)
    + shape(int(8.7 * I), int(2.85 * I), int(3.63 * I), int(2.35 * I),
            [P_([T("WHY DIFFERENT", 14, True, SAFFRON)])]
            + [P_([T("•  " + t, 11, False, WHITE)]) for t in [
                "Voice notes need internet + MBs; dead in blackouts.",
                "Radios: one language, no translation, extra hardware.",
                "Cloud STT: proprietary, needs network, leaks voice.",
                "Text-mesh excludes non-literate users.",
                "Single-model STT fails the south (CER 0.45–0.61)."]],
            fill=CARD, line=SAFFRON)
    + shape(int(0.5 * I), int(5.3 * I), int(12.33 * I), int(1.55 * I),
            [P_([T("KEY VALUE PROPOSITION  •  42 B transcript vs 48,000 B PCM ≈1,100× less data  •  "
                    "CER 0.03–0.34  •  467 + 15 tests green  •  APK 270 MB  •  CPU-only", 12, True, SAFFRON),
                 T("   [all: Measured, device 3353f694, Sep 2026, India]", 10, False, WHITE)]),
             P_([T("Wire [Measured]: ", 11, True, WHITE),
                 T("50 B/datagram × 12 FEC shards = 6,600 B TX/msg (11 broadcast dests) ≈7× vs PCM; "
                   "≤38 B semantic frame engine-tested (18–24 B) but NOT wired into TX — raw UTF-8 since b51be73. "
                   "Fine-tune [Target, not yet run]: P1 shipped (south-indic) → P2 Kathbath 1,700 h + Vaani 7,000 h "
                   "(AI4Bharat/ARTPARK, India) → P3 synthetic disaster vocabulary", 11, False, WHITE)])],
            fill="2A1A08", line=SAFFRON)
    + footer(2)
)

# ================= SLIDE 3 — technical =================
s3 = (
    header("TECHNICAL APPROACH", "Sender → mesh → receiver")
    + shape(int(0.5 * I), TOP, int(12.33 * I), int(0.95 * I),
            [P_([T("16 kHz PCM  →  Silero VAD  →  Hybrid STT (Conformer / Whisper)  →  "
                    "UTF-8 transcript  →  ChaCha20-Poly1305 + RS-FEC (K=8, M=4)  →  "
                    "UDP / Wi-Fi Direct / BT  →  "
                    "TTS  →  Voice / Siren",
                    13, True, WHITE)], align="ctr")],
            fill=CARD, line=TEAL)
    + shape(COL_L["x"], int(3.25 * I), COL_L["w"], int(3.5 * I),
            [P_([T("STACK", 13, True, TEAL)], spaceAfter=150)]
            + bullets([
                ("App + audio:",
                 "Kotlin/Coroutines; C++20 + Oboe 16 kHz mono; JNI bridge."),
                ("AI on CPU only:",
                 "Silero VAD 2.3 MB + Conformer INT8 + whisper.cpp Q8_0; -O2, 4 threads."),
                ("Store + forward:",
                 "hand-rolled binary frames, Room/SQLite audit log, background queue."),
            ], size=14),
            fill=CARD, line="24344F")
    + shape(COL_R["x"], int(3.25 * I), COL_R["w"], int(3.5 * I),
            [P_([T("MODES & PACKET", 13, True, TEAL)], spaceAfter=150)]
            + bullets([
                ("Modes:",
                 "PTT walkie-talkie • normal chat • SOS siren broadcast."),
                ("Packet:",
                 "40 B header (magic, ttl, seq, callsigns, shard idx) + RS shard; AEAD tag, no CRC."),
                ("Survivability:",
                 "Cauchy RS GF(2⁸) K=8/M=4 — recovers any 4 of 12 shards lost."),
            ], size=14),
            fill=CARD, line="24344F")
    + footer(3)
)

# ================= SLIDE 4 — feasibility =================
s4 = (
    header("FEASIBILITY & VIABILITY", "Measured on-device, not slides")
    + shape(COL_L["x"], TOP, COL_L["w"], int(4.6 * I),
            [P_([T("VALIDATION  (measured)", 13, True, TEAL)], spaceAfter=150)]
            + bullets([
                ("467 backend + 15 integration tests green;",
                 "Sep 2026 run (10 skipped); transport 4/4."),
                ("TX on 3353f694 (42 B text):",
                 "50 B/datagram × 12 FEC shards = 6,600 B/msg (11 broadcast dests) "
                 "vs 48,000 B PCM → ≈7× wire, ≈1,100× payload "
                 "(English; Indic ≈3 B/char → 500–800×)."),
                ("≤38 B frame engine-tested (18–24 B) but NOT in TX;",
                 "raw UTF-8 sent since b51be73 — semantic codes fabricated speech."),
                ("CER 0.03–0.34 [Measured, STT_GATE_RESULTS.md, Sep 2026];",
                 "APK 270 MB (≤300 cap); CPU-only, power draw Not Yet Tested."),
                ("Scales [Target]:",
                 "2-node PTT → 10-node team → multi-hop; multi-node Not Yet Tested."),
            ], size=13),
            fill=CARD, line="24344F")
    + shape(COL_R["x"], TOP, COL_R["w"], int(4.6 * I),
            [P_([T("RISKS → FIXES", 13, True, TEAL)], spaceAfter=150)]
            + bullets([
                ("TX amplification [Measured] →",
                 "11 broadcast dests × 12 shards = 6.6 kB/msg; fan-out de-dup open."),
                ("Pause-trigger sentences [Target] →",
                 "not built; PTT release + 10 s silence auto-stop today."),
                ("Small RAM phones →",
                 "INT8/Q8_0 models + lazy load (gated langs only)."),
                ("Dialect errors →",
                 "P2 fine-tune on Kathbath + Vaani corpora."),
                ("Packet loss / collisions →",
                 "Cauchy RS K=8/M=4 + CSMA/CA channel lock; VAD noise gate."),
            ], size=13),
            fill=CARD, line="24344F")
    + footer(4)
)

# ================= SLIDE 5 — impact =================
s5 = (
    header("IMPACT & VALUE", "Who gains, and how much")
    + shape(COL_L["x"], TOP, COL_L["w"], int(4.6 * I),
            [P_([T("PEOPLE & OPS", 13, True, TEAL)], spaceAfter=150)]
            + bullets([
                ("Social:",
                 "voice-in/voice-out in 10 languages; works for non-literate users."),
                ("Admin:",
                 "NDRF/police/fire/medical coordinate cross-language; SOS siren override."),
                ("Economic:",
                 "runs on ordinary phones; zero cloud/data bills."),
            ], size=14),
            fill=CARD, line="24344F")
    + shape(COL_R["x"], TOP, COL_R["w"], int(4.6 * I),
            [P_([T("TRUST & NATION", 13, True, TEAL)], spaceAfter=150)]
            + bullets([
                ("Privacy:",
                 "voice never leaves the phone; open-source auditable stack."),
                ("Green:",
                 "≈1,100× less data at payload (42 B vs 48,000 B PCM); wire 6.6 kB/msg incl. FEC; longer handset life."),
                ("Atmanirbhar:",
                 "indigenous stack, works through total grid/internet blackout."),
            ], size=14),
            fill=CARD, line="24344F")
    + footer(5)
)

# ================= SLIDE 6 — references =================
s6 = (
    header("RESEARCH & REFERENCES", "Every claim traces to a source")
    + shape(COL_L["x"], TOP, COL_L["w"], int(4.6 * I),
            [P_([T("PROBLEM + AI", 13, True, TEAL)], spaceAfter=150)]
            + bullets([
                "ITU emergency-telecom handbook; NDMA plan; ISRO/SIH-2026 PS.",
                "AI4Bharat IndicConformer + Kathbath (IIT-M).",
                "ARTPARK-Vaani 7,000 h Indic corpus (IISc) — P2 tuning data.",
                "parambharat/whisper-tiny-south-indic (HF) + whisper.cpp.",
                "snakers4/silero-vad — speech gating pre-STT; no version string in shipped ONNX.",
            ], size=13),
            fill=CARD, line="24344F")
    + shape(COL_R["x"], TOP, COL_R["w"], int(4.6 * I),
            [P_([T("MARKET + PROOF", 13, True, TEAL)], spaceAfter=150)]
            + bullets([
                "MarketsandMarkets, Critical Communications, Global, 2024: $18.4B (2024) → $34.8B (2030), 11.2% CAGR.",
                "TRAI Performance Indicators, India, 2024: ~1.19B wireless subscribers (Est., unverified here).",
                "iTantra audit, Sep 2026: 467 backend + 15 integration tests green; TX path measured 50 B/datagram × 12 FEC shards.",
                "STT_GATE_RESULTS.md, Sep 2026: laptop CER gate + on-device parity.",
            ], size=13),
            fill=CARD, line="24344F")
    + footer(6)
)

SLIDES = [s1, s2, s3, s4, s5, s6]

# ---- package parts ----
CT = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<Types xmlns="{CP}">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
    '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
    '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
    + "".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, 7))
    + '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
    '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
    '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
    "</Types>")

RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<Relationships xmlns="{REL}">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
    '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
    "</Relationships>")

PRES_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<Relationships xmlns="{REL}">'
    + "".join(
        f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>'
        for i in range(1, 7))
    + '<Relationship Id="rId7" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    '<Relationship Id="rId8" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>'
    "</Relationships>")

PRES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<p:presentation xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}">'
    "<p:sldMasterIdLst><p:sldMasterId r:id=\"rId7\"/></p:sldMasterIdLst>"
    "<p:sldIdLst>"
    + "".join(f"<p:sldId id=\"{255 + i}\" r:id=\"rId{i}\"/>" for i in range(1, 7))
    + "</p:sldIdLst>"
    f'<p:sldSz cx="{SW}" cy="{SH}" type="screen16x9"/>'
    "<p:notesSz cx=\"6858000\" cy=\"9144000\"/></p:presentation>")

MASTER = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<p:sldMaster xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}"><p:cSld>'
    '<p:bg><p:bgPr><a:solidFill><a:srgbClr val="0B1E3A"/></a:solidFill></p:bgPr></p:bg>'
    '<p:spTree><p:nvGrpSpPr><p:cNvPr id="0" name=""/>'
    "<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>"
    '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/>'
    f'<a:ext cx="{SW}" cy="{SH}"/><a:chOff x="0" y="0"/><a:chExt cx="{SW}" cy="{SH}"/>'
    "</a:xfrm></p:grpSpPr></p:spTree></p:cSld>"
    '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" '
    'accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" '
    'accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
    '<p:sldLayoutIdLst><p:sldLayoutId r:id="rId1"/></p:sldLayoutIdLst>'
    "<p:txStyles><p:titleStyle><a:lvl1pPr><a:defRPr sz=\"4400\">"
    '<a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>'
    '<a:latin typeface="Calibri"/></a:defRPr></a:lvl1pPr></p:titleStyle>'
    "<p:bodyStyle><a:lvl1pPr><a:defRPr sz=\"1800\">"
    '<a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>'
    '<a:latin typeface="Calibri"/></a:defRPr></a:lvl1pPr></p:bodyStyle>'
    "<p:otherStyle><a:lvl1pPr><a:defRPr sz=\"1800\">"
    '<a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>'
    '<a:latin typeface="Calibri"/></a:defRPr></a:lvl1pPr></p:otherStyle>'
    "</p:txStyles></p:sldMaster>")

MASTER_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<Relationships xmlns="{REL}">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>'
    "</Relationships>")

LAYOUT = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<p:sldLayout xmlns:a="{A}" xmlns:r="{R}" xmlns:p="{P}" type="blank" preserve="1">'
    "<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id=\"0\" name=\"\"/>"
    "<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>"
    '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/>'
    f'<a:ext cx="{SW}" cy="{SH}"/><a:chOff x="0" y="0"/><a:chExt cx="{SW}" cy="{SH}"/>'
    "</a:xfrm></p:grpSpPr></p:spTree></p:cSld>"
    '<p:clrMapOvr><a:overrideClrMapping bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" '
    'accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" '
    'accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
    "</p:clrMapOvr></p:sldLayout>")

LAYOUT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<Relationships xmlns="{REL}">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>'
    "</Relationships>")

THEME = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<a:theme xmlns:a="{A}" name="iTantra"><a:themeElements><a:clrScheme name="iTantra">'
    "<a:dk1><a:srgbClr val=\"0B1E3A\"/></a:dk1><a:lt1><a:srgbClr val=\"FFFFFF\"/></a:lt1>"
    "<a:dk2><a:srgbClr val=\"16294A\"/></a:dk2><a:lt2><a:srgbClr val=\"C9D4E3\"/></a:lt2>"
    "<a:accent1><a:srgbClr val=\"FF6B1A\"/></a:accent1><a:accent2><a:srgbClr val=\"00C2A8\"/></a:accent2>"
    "<a:accent3><a:srgbClr val=\"3A86FF\"/></a:accent3><a:accent4><a:srgbClr val=\"8338EC\"/></a:accent4>"
    "<a:accent5><a:srgbClr val=\"FFBE0B\"/></a:accent5><a:accent6><a:srgbClr val=\"FB5607\"/></a:accent6>"
    "<a:hlink><a:srgbClr val=\"3A86FF\"/></a:hlink><a:folHlink><a:srgbClr val=\"8338EC\"/></a:folHlink>"
    "</a:clrScheme>"
    "<a:fmtScheme name=\"iTantra\"><a:fillStyleLst>"
    "<a:solidFill><a:schemeClr val=\"phClr\"/></a:solidFill>"
    "</a:fillStyleLst><a:lnStyleLst>"
    "<a:ln w=\"6350\"><a:solidFill><a:schemeClr val=\"phClr\"/></a:solidFill></a:ln>"
    "</a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle>"
    "</a:effectStyleLst><a:bgFillStyleLst>"
    "<a:solidFill><a:schemeClr val=\"phClr\"/></a:solidFill>"
    "</a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>")

CORE = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/">'
    "<dc:title>iTantra — SIH 2026</dc:title><dc:creator>Team iTantra</dc:creator>"
    "</cp:coreProperties>")

APP = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
    "<Application>iTantra build script</Application><PresentationFormat>Widescreen</PresentationFormat>"
    "<Slides>6</Slides></Properties>")


def slide_rels():
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{REL}">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
        "</Relationships>")


parts = {
    "[Content_Types].xml": CT,
    "_rels/.rels": RELS,
    "ppt/presentation.xml": PRES,
    "ppt/_rels/presentation.xml.rels": PRES_RELS,
    "ppt/slideMasters/slideMaster1.xml": MASTER,
    "ppt/slideMasters/_rels/slideMaster1.xml.rels": MASTER_RELS,
    "ppt/slideLayouts/slideLayout1.xml": LAYOUT,
    "ppt/slideLayouts/_rels/slideLayout1.xml.rels": LAYOUT_RELS,
    "ppt/theme/theme1.xml": THEME,
    "docProps/core.xml": CORE,
    "docProps/app.xml": APP,
}
for idx, shapes in enumerate(SLIDES, 1):
    parts[f"ppt/slides/slide{idx}.xml"] = slide_xml(shapes)
    parts[f"ppt/slides/_rels/slide{idx}.xml.rels"] = slide_rels()

# validate: every part must be well-formed XML
for name, body in parts.items():
    ET.fromstring(body)
print(f"all {len(parts)} parts: XML well-formed")

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for name, body in parts.items():
        z.writestr(name, body.encode("utf-8"))
print("wrote", OUT)
