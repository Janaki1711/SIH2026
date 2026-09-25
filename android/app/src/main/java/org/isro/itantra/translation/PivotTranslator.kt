package org.isro.itantra.translation

/**
 * Offline disaster-gloss translator used when ML Kit has no model for a
 * language pair (ml / or / pa have no ML Kit model at all).
 *
 * Design — English as the pivot/median language:
 *   1. Every source-language token is looked up in a language-specific index
 *      that maps it to a canonical concept (e.g. ml "ആംബുലൻസ്" → concept
 *      "ambulance"). English surface forms are additionally indexed into
 *      every language, so loan-words and mixed-script sentences still match.
 *   2. The concept is realized in the target language from the same table.
 *
 * Semantics: this is a *disaster-vocabulary gloss*, not full translation.
 * Word order of unknown tokens is preserved as-is. It returns **null** when
 * no concept in the source text is recognised — the caller must then show the
 * original text with an honest "[lang]" label instead of pretending the text
 * was translated.
 *
 * Scope: offline fallback only. ML Kit (English pivot) remains the primary
 * path for the 8 supported languages.
 */
object PivotTranslator {

    private val TOKEN_PATTERN = Regex("\\p{L}+")

    /**
     * concept → language → surface form.
     * The surface form doubles as (a) the output for that language and
     * (b) an accepted source token for that language.
     *
     * Languages: en (pivot), hi, ta, te, mr, bn, kn, ml, gu, or, pa.
     */
    private val OUTPUT: Map<String, Map<String, String>> = mapOf(
        "help" to mapOf(
            "en" to "help", "hi" to "मदद", "ta" to "உதவி", "te" to "సహాయం",
            "mr" to "मदत", "bn" to "সাহায্য", "kn" to "ಸಹಾಯ", "ml" to "സഹായം",
            "gu" to "મદદ", "or" to "ସାହାଯ୍ୟ", "pa" to "ਮਦਦ"
        ),
        "ambulance" to mapOf(
            "en" to "ambulance", "hi" to "एम्बुलेंस", "ta" to "ஆம்புலன்ஸ்", "te" to "అంబులెన్స్",
            "mr" to "रुग्णवाहिक", "bn" to "অ্যাম্বুলেন্স", "kn" to "ಆಂಬ್ಯುಲೆನ್ಸ್", "ml" to "ആംബുലൻസ്",
            "gu" to "એમ્બ્યુલન્સ", "or" to "ଆମ୍ବୁଲେନ୍ସ", "pa" to "ਐਂਬੁਲੈਂਸ"
        ),
        "fire" to mapOf(
            "en" to "fire", "hi" to "आग", "ta" to "தீ", "te" to "మంట",
            "mr" to "आगी", "bn" to "আগুন", "kn" to "ಬೆಂಕಿ", "ml" to "തീ",
            "gu" to "આગ", "or" to "ଅଗ୍ନି", "pa" to "ਅੱਗ"
        ),
        "flood" to mapOf(
            "en" to "flood", "hi" to "बाढ़", "ta" to "வெள்ளம்", "te" to "వరద",
            "mr" to "पूर", "bn" to "বন্যা", "kn" to "ಪ್ರವಾಹ", "ml" to "പ്രളയം",
            "gu" to "પૂર", "or" to "ବନ୍ୟା", "pa" to "ਹੜ੍ਹ"
        ),
        "water" to mapOf(
            "en" to "water", "hi" to "पानी", "ta" to "நீர்", "te" to "నీరు",
            "mr" to "पाणी", "bn" to "পানি", "kn" to "ನೀರು", "ml" to "വെള്ളം",
            "gu" to "પાણી", "or" to "ପାଣି", "pa" to "ਪਾਣੀ"
        ),
        "danger" to mapOf(
            "en" to "danger", "hi" to "खतरा", "ta" to "ஆபத்து", "te" to "ప్రమాదం",
            "mr" to "धोका", "bn" to "বিপদ", "kn" to "ಅಪಾಯ", "ml" to "അപകടം",
            "gu" to "જોખમ", "or" to "ବିପଦ", "pa" to "ਖ਼ਤਰਾ"
        ),
        "emergency" to mapOf(
            "en" to "emergency", "hi" to "आपातकाल", "ta" to "அவசரநிலை", "te" to "అత్యవసర స్థితి",
            "mr" to "आणीबाणी", "bn" to "জরুরি অবস্থা", "kn" to "ತುರ್ತು ಸ್ಥಿತಿ", "ml" to "അടിയന്തരാവസ്ഥ",
            "gu" to "કટોકટી", "or" to "ଜରୁରୀକାଳୀନ", "pa" to "ਹੁਰੰਮੀ"
        ),
        "urgent" to mapOf(
            "en" to "urgent", "hi" to "तुरंत", "ta" to "உடனடி", "te" to "వెంటనే",
            "mr" to "त्वरित", "bn" to "তাড়াতাড়ি", "kn" to "ತಕ್ಷಣ", "ml" to "ഉടൻ",
            "gu" to "તાત્કાલિક", "or" to "ତୁରନ୍ତ", "pa" to "ਤੁਰੰਤ"
        ),
        "send" to mapOf(
            "en" to "send", "hi" to "भेजें", "ta" to "அனுப்பு", "te" to "పంపండి",
            "mr" to "पाठवा", "bn" to "পাঠান", "kn" to "ಕಳುಹಿಸಿ", "ml" to "അയക്കുക",
            "gu" to "મોકલો", "or" to "ପଠାନ୍ତୁ", "pa" to "ਭੇਜੋ"
        ),
        "team" to mapOf(
            "en" to "team", "hi" to "दल", "ta" to "குழு", "te" to "బృందం",
            "mr" to "पथक", "bn" to "দল", "kn" to "ತಂಡ", "ml" to "സംഘം",
            "gu" to "ટીમ", "or" to "ଦଳ", "pa" to "ਟੋਲੀ"
        ),
        "rescue" to mapOf(
            "en" to "rescue", "hi" to "बचाव", "ta" to "மீட்பு", "te" to "రక్షణ",
            "mr" to "बचाव", "bn" to "উদ্ধার", "kn" to "ರಕ್ಷಣೆ", "ml" to "രക്ഷ",
            "gu" to "બચાવ", "or" to "ଉଦ୍ଧାର", "pa" to "ਬਚਾਅ"
        ),
        "injured" to mapOf(
            "en" to "injured", "hi" to "घायल", "ta" to "காயம்", "te" to "గాయం",
            "mr" to "जखमी", "bn" to "আহত", "kn" to "ಗಾಯ", "ml" to "പരിക്ക്",
            "gu" to "ઘાયલ", "or" to "ଆହତ", "pa" to "ਜ਼ਖ਼ਮੀ"
        ),
        "people" to mapOf(
            "en" to "people", "hi" to "लोग", "ta" to "மக்கள்", "te" to "ప్రజలు",
            "mr" to "लोक", "bn" to "মানুষ", "kn" to "ಜನ", "ml" to "ആളുകൾ",
            "gu" to "લોકો", "or" to "ଲୋକ", "pa" to "ਲੋਕ"
        ),
        "trapped" to mapOf(
            "en" to "trapped", "hi" to "फंसे", "ta" to "சிக்கி", "te" to "చిక్కుకున్న",
            "mr" to "अडकले", "bn" to "আটকে", "kn" to "ಸಿಕ್ಕಿ", "ml" to "കുടുങ്ങി",
            "gu" to "ફસાયેલા", "or" to "ଫସିଯାଇ", "pa" to "ਫਸੇ"
        ),
        "food" to mapOf(
            "en" to "food", "hi" to "खाना", "ta" to "உணவு", "te" to "ఆహారం",
            "mr" to "अन्न", "bn" to "খাবার", "kn" to "ಊಟ", "ml" to "ഭക്ഷണം",
            "gu" to "ખોરાક", "or" to "ଖାଦ୍ୟ", "pa" to "ਖਾਣਾ"
        ),
        "medicine" to mapOf(
            "en" to "medicine", "hi" to "दवा", "ta" to "மருந்து", "te" to "మందు",
            "mr" to "औषध", "bn" to "ওষুধ", "kn" to "ಔಷಧ", "ml" to "മരുന്ന്",
            "gu" to "દવા", "or" to "ଔଷଧ", "pa" to "ਦਵਾਈ"
        ),
        "doctor" to mapOf(
            "en" to "doctor", "hi" to "डॉक्टर", "ta" to "மருத்துவர்", "te" to "వైద్యుడు",
            "mr" to "डॉक्टर", "bn" to "ডাক্তার", "kn" to "ವೈದ್ಯ", "ml" to "ഡോക്ടർ",
            "gu" to "ડૉક્ટર", "or" to "ଡାକ୍ତର", "pa" to "ਡਾਕਟਰ"
        ),
        "hospital" to mapOf(
            "en" to "hospital", "hi" to "अस्पताल", "ta" to "மருத்துவமனை", "te" to "ఆసుపత్రి",
            "mr" to "रुग्णालय", "bn" to "হাসপাতাল", "kn" to "ಆಸ್ಪತ್ರೆ", "ml" to "ആശുപത്രി",
            "gu" to "હોસ્પિટલ", "or" to "ଡାକ୍ତରଖାନା", "pa" to "ਹਸਪਤਾਲ"
        ),
        "shelter" to mapOf(
            "en" to "shelter", "hi" to "आश्रय", "ta" to "தங்குமிடம்", "te" to "ఆశ్రయం",
            "mr" to "शरण", "bn" to "আশ্রয়", "kn" to "ಆಶ್ರಯ", "ml" to "ആശ്രയം",
            "gu" to "શરણ", "or" to "ଆଶ୍ରୟ", "pa" to "ਸ਼ਰਣ"
        ),
        "road" to mapOf(
            "en" to "road", "hi" to "सड़क", "ta" to "சாலை", "te" to "రహదారి",
            "mr" to "रस्ता", "bn" to "রাস্তা", "kn" to "ರಸ್ತೆ", "ml" to "റോഡ്",
            "gu" to "રસ્તો", "or" to "ରାସ୍ତା", "pa" to "ਸੜਕ"
        ),
        "bridge" to mapOf(
            "en" to "bridge", "hi" to "पुल", "ta" to "பாலம்", "te" to "వంతెన",
            "mr" to "पूल", "bn" to "সেতু", "kn" to "ಸೇತುವೆ", "ml" to "പാലം",
            "gu" to "પુલ", "or" to "ସେତୁ", "pa" to "ਪੁਲ"
        ),
        "school" to mapOf(
            "en" to "school", "hi" to "विद्यालय", "ta" to "பள்ளி", "te" to "పాఠశాల",
            "mr" to "शाळा", "bn" to "স্কুল", "kn" to "ಶಾಲೆ", "ml" to "സ്കൂൾ",
            "gu" to "શાળા", "or" to "ବିଦ୍ୟାଳୟ", "pa" to "ਸਕੂਲ"
        ),
        "missing" to mapOf(
            "en" to "missing", "hi" to "लापता", "ta" to "காணாமல்", "te" to "అదృశ్య",
            "mr" to "गुमला", "bn" to "নিখোঁজ", "kn" to "ನಾಪತ್ತೆ", "ml" to "കാണാതായ",
            "gu" to "ગુમથયેલા", "or" to "ନିଖୋଜ", "pa" to "ਲਾਪਤਾ"
        ),
        "alive" to mapOf(
            "en" to "alive", "hi" to "जीवित", "ta" to "உயிருடன்", "te" to "బ్రతికి",
            "mr" to "जिवंत", "bn" to "জীবিত", "kn" to "ಜೀವಂತ", "ml" to "ജീവനുള്ള",
            "gu" to "જીવિત", "or" to "ଜୀବିତ", "pa" to "ਜਿਊਂਦਾ"
        ),
        "storm" to mapOf(
            "en" to "storm", "hi" to "तूफान", "ta" to "புயல்", "te" to "తుఫాను",
            "mr" to "वादळ", "bn" to "ঝড়", "kn" to "ಬಿರುಗಾಳಿ", "ml" to "കൊടുങ്കാറ്റ്",
            "gu" to "તોફાન", "or" to "ଝଡ଼", "pa" to "ਤੂਫ਼ਾਨ"
        ),
        "earthquake" to mapOf(
            "en" to "earthquake", "hi" to "भूकंप", "ta" to "நிலநடுக்கம்", "te" to "భూకంపం",
            "mr" to "भूकंप", "bn" to "ভূমিকম্প", "kn" to "ಭೂಕಂಪ", "ml" to "ഭൂകമ്പം",
            "gu" to "ભૂકંપ", "or" to "ଭୂକମ୍ପ", "pa" to "ਭੂਕੰਪ"
        ),
        "rain" to mapOf(
            "en" to "rain", "hi" to "बारिश", "ta" to "மழை", "te" to "వర్షం",
            "mr" to "पाऊस", "bn" to "বৃষ্টি", "kn" to "ಮಳೆ", "ml" to "മഴ",
            "gu" to "વરસાદ", "or" to "ବର୍ଷା", "pa" to "ਮੀਂਹ"
        ),
        "night" to mapOf(
            "en" to "night", "hi" to "रात", "ta" to "இரவு", "te" to "రాత్రి",
            "mr" to "रात्री", "bn" to "রাত", "kn" to "ರಾತ್ರಿ", "ml" to "രാത്രി",
            "gu" to "રાત્રિ", "or" to "ରାତ୍ରି", "pa" to "ਰਾਤ"
        ),
        "now" to mapOf(
            "en" to "now", "hi" to "अभी", "ta" to "இப்போது", "te" to "ఇప్పుడు",
            "mr" to "आता", "bn" to "এখন", "kn" to "ಈಗ", "ml" to "ഇപ്പോൾ",
            "gu" to "હવે", "or" to "ବର୍ତ୍ତମାନ", "pa" to "ਹੁਣ"
        ),
        "need" to mapOf(
            "en" to "need", "hi" to "जरूरत", "ta" to "தேவை", "te" to "అవసరం",
            "mr" to "गरज", "bn" to "প্রয়োজন", "kn" to "ಅಗತ್ಯ", "ml" to "ആവശ്യം",
            "gu" to "જરૂર", "or" to "ଆବଶ୍ୟକ", "pa" to "ਲੋੜ"
        ),
        "please" to mapOf(
            "en" to "please", "hi" to "कृपया", "ta" to "தயவுசெய்து", "te" to "దయచేసి",
            "mr" to "कृपया", "bn" to "অনুগ্রহ করে", "kn" to "ದಯವಿಟ್ಟು", "ml" to "ദയവാകി",
            "gu" to "કૃપા કરી", "or" to "ଦୟାକରି", "pa" to "ਕਿਰਪਾ"
        ),
        "evacuate" to mapOf(
            "en" to "evacuate", "hi" to "खाली करें", "ta" to "வெளியேறு", "te" to "ఖాళీ చేయండి",
            "mr" to "रिकामे करा", "bn" to "খালি করুন", "kn" to "ತೆರವುಗೊಳಿಸಿ", "ml" to "ഒഴിയുക",
            "gu" to "ખાલી કરો", "or" to "ଖାଲି କରନ୍ତୁ", "pa" to "ਖਾਲੀ ਕਰੋ"
        ),
        "safe" to mapOf(
            "en" to "safe", "hi" to "सुरक्षित", "ta" to "பாதுகாப்பான", "te" to "సురక్షిత",
            "mr" to "सुरक्षित", "bn" to "নিরাপদ", "kn" to "ಸುರಕ್ಷಿತ", "ml" to "സുരക്ഷിത",
            "gu" to "સુરક્ષિત", "or" to "ସୁରକ୍ଷିତ", "pa" to "ਸੁਰੱਖਿਅਤ"
        ),
        "signal" to mapOf(
            "en" to "signal", "hi" to "संकेत", "ta" to "சமிக்ஞை", "te" to "సంకేతం",
            "mr" to "संकेत", "bn" to "সংকেত", "kn" to "ಸಂಕೇತ", "ml" to "സംകേതം",
            "gu" to "સંકેત", "or" to "ସଙ୍କେତ", "pa" to "ਸੰਕੇਤ"
        ),
        "battery" to mapOf(
            "en" to "battery", "hi" to "बैटरी", "ta" to "பேட்டரி", "te" to "బ్యాటరీ",
            "mr" to "बॅटरी", "bn" to "ব্যাটারি", "kn" to "ಬ್ಯಾಟರಿ", "ml" to "ബാറ്ററി",
            "gu" to "બેટરી", "or" to "ବାଟେରୀ", "pa" to "ਬੈਟਰੀ"
        ),
        "child" to mapOf(
            "en" to "child", "hi" to "बच्चा", "ta" to "குழந்தை", "te" to "పిల్ల",
            "mr" to "मूल", "bn" to "শিশু", "kn" to "ಮಗು", "ml" to "കുട്ടി",
            "gu" to "બાળક", "or" to "ଶିଶୁ", "pa" to "ਬੱਚਾ"
        ),
        "family" to mapOf(
            "en" to "family", "hi" to "परिवार", "ta" to "குடும்பம்", "te" to "కుటుంబం",
            "mr" to "कुटुंब", "bn" to "পরিবার", "kn" to "ಕುಟುಂಬ", "ml" to "കുടുംബം",
            "gu" to "પરિવાર", "or" to "ପରିବାର", "pa" to "ਪਰਿਵਾਰ"
        ),
        "wait" to mapOf(
            "en" to "wait", "hi" to "प्रतीक्षा", "ta" to "காத்திரு", "te" to "వేచి ఉండి",
            "mr" to "प्रतीक्षा", "bn" to "অপেক্ষা", "kn" to "ಕಾಯಿರಿ", "ml" to "കാത്തിരിക്കൂ",
            "gu" to "રાહ જુઓ", "or" to "ଅପେକ୍ଷା", "pa" to "ਉਡੀਕੋ"
        ),
        "come" to mapOf(
            "en" to "come", "hi" to "आओ", "ta" to "வா", "te" to "రండి",
            "mr" to "या", "bn" to "আসো", "kn" to "ಬನ್ನಿ", "ml" to "വരൂ",
            "gu" to "આવો", "or" to "ଆସନ୍ତୁ", "pa" to "ਆਓ"
        ),
        "helicopter" to mapOf(
            "en" to "helicopter", "hi" to "हेलीकॉप्टर", "ta" to "ஹெலிகாப்டர்", "te" to "హెలికాప్టర్",
            "mr" to "हेलिकॉप्टर", "bn" to "হেলিকপ্টার", "kn" to "ಹೆಲಿಕಾಪ್ಟರ್", "ml" to "ഹെലികോപ്ടർ",
            "gu" to "હેલિકોપ્ટર", "or" to "ହେଲିକପ୍ଟର", "pa" to "ਹੈਲੀਕਾਪਟਰ"
        ),
        "police" to mapOf(
            "en" to "police", "hi" to "पुलिस", "ta" to "காவல்துறை", "te" to "పోలీసు",
            "mr" to "पोलिस", "bn" to "পুলিশ", "kn" to "ಪೊಲೀಸ್", "ml" to "പൊലീസ്",
            "gu" to "પોલીસ", "or" to "ପୋଲିସ", "pa" to "ਪੁਲਿਸ"
        ),
        "army" to mapOf(
            "en" to "army", "hi" to "सेना", "ta" to "இராணுவம்", "te" to "సైన్యం",
            "mr" to "सैन्य", "bn" to "সেনা", "kn" to "ಸೇನೆ", "ml" to "സേന",
            "gu" to "સેના", "or" to "ସେନା", "pa" to "ਫੌਜ"
        ),
        "camp" to mapOf(
            "en" to "camp", "hi" to "शिविर", "ta" to "முகாம்", "te" to "శిబిరం",
            "mr" to "शिबिर", "bn" to "শিবির", "kn" to "ಶಿಬಿರ", "ml" to "ക്യാമ്പ്",
            "gu" to "શિબિર", "or" to "ଶିବିର", "pa" to "ਕੈਂਪ"
        ),
        "dead" to mapOf(
            "en" to "dead", "hi" to "मृत", "ta" to "இறந்த", "te" to "మృతి",
            "mr" to "मृत", "bn" to "মৃত", "kn" to "ಮೃತ", "ml" to "മരിച്ച",
            "gu" to "મૃત", "or" to "ମୃତ", "pa" to "ਮਰੇ"
        )
    )

    /**
     * concept → language → extra accepted source forms (inflections,
     * plurals, synonyms an ML Kit / speaker may produce). English aliases
     * matter most: the EN pivot hop feeds English text back into this table.
     */
    private val ALIASES: Map<String, Map<String, List<String>>> = mapOf(
        "help" to mapOf("en" to listOf("help", "helps", "helping", "helped", "aid", "aids", "assist", "assistance")),
        "ambulance" to mapOf("en" to listOf("ambulance", "ambulances")),
        "fire" to mapOf("en" to listOf("fire", "fires", "burning", "blaze", "blazes")),
        "flood" to mapOf("en" to listOf("flood", "floods", "flooding", "inundation")),
        "water" to mapOf("en" to listOf("water", "waters")),
        "danger" to mapOf("en" to listOf("danger", "dangers", "dangerous", "hazard", "hazards", "hazardous", "risky")),
        "emergency" to mapOf("en" to listOf("emergency", "emergencies")),
        "urgent" to mapOf("en" to listOf("urgent", "urgency", "immediately", "immediate", "asap", "hurry", "quickly")),
        "send" to mapOf("en" to listOf("send", "sends", "sending", "sent")),
        "team" to mapOf("en" to listOf("team", "teams", "unit", "units", "crew", "crews")),
        "rescue" to mapOf("en" to listOf("rescue", "rescues", "rescued", "rescuing", "save", "saving", "saved")),
        "injured" to mapOf("en" to listOf("injured", "injury", "injuries", "wounded", "hurt", "casualty", "casualties")),
        "people" to mapOf("en" to listOf("people", "person", "persons", "someone", "somebody", "anybody", "anyone")),
        "trapped" to mapOf("en" to listOf("trapped", "trap", "traps", "stuck", "marooned", "stranded")),
        "food" to mapOf("en" to listOf("food", "foods", "meal", "meals", "ration", "rations")),
        "medicine" to mapOf("en" to listOf("medicine", "medicines", "drug", "drugs", "medication")),
        "doctor" to mapOf("en" to listOf("doctor", "doctors", "physician")),
        "hospital" to mapOf("en" to listOf("hospital", "hospitals", "clinic", "clinics")),
        "shelter" to mapOf("en" to listOf("shelter", "shelters", "refuge", "refuges")),
        "road" to mapOf("en" to listOf("road", "roads", "highway", "highways", "route", "routes", "street", "streets")),
        "bridge" to mapOf("en" to listOf("bridge", "bridges")),
        "school" to mapOf("en" to listOf("school", "schools")),
        "missing" to mapOf("en" to listOf("missing", "lost", "disappeared")),
        "alive" to mapOf("en" to listOf("alive", "survivor", "survivors", "survived", "surviving", "living")),
        "storm" to mapOf("en" to listOf("storm", "storms", "cyclone", "cyclones", "hurricane", "hurricanes", "typhoon")),
        "earthquake" to mapOf("en" to listOf("earthquake", "earthquakes", "quake", "quakes", "tremor", "tremors")),
        "rain" to mapOf("en" to listOf("rain", "rains", "raining", "rainfall")),
        "night" to mapOf("en" to listOf("night", "nights", "midnight")),
        "now" to mapOf("en" to listOf("now", "currently")),
        "need" to mapOf("en" to listOf("need", "needs", "needed", "require", "required", "requirement", "requirements")),
        "please" to mapOf("en" to listOf("please", "kindly")),
        "evacuate" to mapOf("en" to listOf("evacuate", "evacuated", "evacuating", "vacate", "flee")),
        "safe" to mapOf("en" to listOf("safe", "safely", "safety", "secure", "securely")),
        "signal" to mapOf("en" to listOf("signal", "signals", "beacon", "beacons")),
        "battery" to mapOf("en" to listOf("battery", "batteries")),
        "child" to mapOf("en" to listOf("child", "children", "kid", "kids", "baby", "babies")),
        "family" to mapOf("en" to listOf("family", "families", "relative", "relatives")),
        "wait" to mapOf("en" to listOf("wait", "waiting", "waits", "stay", "staying")),
        "come" to mapOf("en" to listOf("come", "comes", "coming", "came", "arrive", "arrives", "arrived")),
        "helicopter" to mapOf("en" to listOf("helicopter", "helicopters", "chopper", "choppers")),
        "police" to mapOf("en" to listOf("police", "cops")),
        "army" to mapOf("en" to listOf("army", "troop", "troops", "soldier", "soldiers", "forces")),
        "camp" to mapOf("en" to listOf("camp", "camps", "tent", "tents")),
        "dead" to mapOf("en" to listOf("dead", "died", "death", "deceased"))
    )

    /** lang → (token → concept). Built once, lazily. */
    private val INDEX: Map<String, Map<String, String>> by lazy {
        val idx = HashMap<String, HashMap<String, String>>()
        fun add(lang: String, token: String, concept: String) {
            idx.getOrPut(lang) { HashMap() }.putIfAbsent(token, concept)
        }
        for ((concept, perLang) in OUTPUT) {
            for ((lang, form) in perLang) add(lang, form.lowercase(), concept)
        }
        for ((concept, perLang) in ALIASES) {
            for ((lang, forms) in perLang) {
                for (form in forms) add(lang, form.lowercase(), concept)
            }
        }
        // English forms are additionally accepted in EVERY language index:
        // speakers mix English loan-words into Indic sentences, and the
        // EN-pivot hop returns English text. Snapshot "en" first so we never
        // mutate a map while iterating it.
        val enIndex = HashMap(idx["en"] ?: HashMap())
        val allLangs = OUTPUT.values.first().keys
        for (lang in allLangs) {
            for ((form, concept) in enIndex) add(lang, form, concept)
        }
        idx
    }

    /**
     * Gloss [text] from [sourceLang] into [targetLang] via canonical concepts.
     *
     * @return the glossed text, or **null** when no recognised concept was
     * found (caller must fall back to the original text + honest label).
     */
    fun translate(text: String, sourceLang: String, targetLang: String): String? {
        if (text.isBlank() || sourceLang == targetLang) return null
        val srcIndex = INDEX[sourceLang] ?: return null
        val sb = StringBuilder()
        var last = 0
        var replaced = 0
        for (m in TOKEN_PATTERN.findAll(text)) {
            sb.append(text, last, m.range.first)
            val concept = srcIndex[m.value.lowercase()]
            val outForm = concept?.let { OUTPUT[it]?.get(targetLang) }
            if (outForm != null) {
                sb.append(outForm)
                replaced++
            } else {
                sb.append(m.value)
            }
            last = m.range.last + 1
        }
        sb.append(text, last, text.length)
        return if (replaced == 0) null else sb.toString()
    }
}
