package org.isro.itantra.audio

import android.content.Context
import android.util.Log
import java.io.BufferedReader
import java.io.InputStreamReader

class SpellCorrector(private val context: Context) {
    // Cache for loaded language dictionaries: word -> frequency
    private val dictionaries = HashMap<String, HashMap<String, Long>>()
    // Cache for phonetic index: phoneticKey -> list of (word, freq)
    private val phoneticDictionaries = HashMap<String, HashMap<String, ArrayList<Pair<String, Long>>>>()
    
    @Volatile
    private var currentLang: String = "en"

    // Minimum believable dictionary size — real wordlists have thousands of
    // entries; the corrupted hi/kn asset stubs parse to a handful of mojibake
    // lines (see loadDictionary).
    private companion object {
        const val MIN_DICT_WORDS = 50
    }

    // Alphabets for edits (insertions and replacements)
    private val alphabets = mapOf(
        "en" to "abcdefghijklmnopqrstuvwxyz",
        "hi" to "अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहृािीुूेैोौंः", // Devanagari (Hindi/Marathi)
        "mr" to "अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहृािीुूेैोौंः",
        "ta" to "அஆஇஈஉஊஎஏஐஒஓஔகஙசஞடணதநநபமயரறலளழவஷஸஹ்ாிீுூெேைொோௌ", // Tamil
        "te" to "అఆఇఈఉఊఋఎఏఐఒఓఔకఖగఘఙచఛజఝఞటఠడఢణతథదధనపఫబభమయరలవశషసహాిీుూెేైొోౌ్", // Telugu
        "bn" to "অআইঈউঊঋএঐওঔকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহািীুূেৈোৌ্", // Bengali
        "gu" to "અઅઇઈઉઊઋએઐઓઔકખગઘઙચછજઝઞટઠડઢણતથદધનપફબભમયરલવશષસહાિીુૂેૈોૌ્", // Gujarati
        "pa" to "ਅਆਇਈਉਊਏਐਓਔਕਖਗਘਙਚਛਜਝਞਟਠਡਢਣਤਥదਧਨਪਫਬਭਮਯਰਲਵਸ਼ਸਹਾਿੀੁੂੇੈੋੌ੍", // Punjabi
        "kn" to "ಅಆಇಈಉಊಋಎಏಐಒಓಔಕಖಗಘಙಚಛಜಝಞಟಠಡಢಣತಥದಧನಪಫಬಭಮಯರಲವಶಷಸಹಾિೀುೂೆೇೈೊೋೌ್", // Kannada
        "ml" to "അആഇഈഉഊഋഎഏഐഒഓഔകഖഗഘങചഛജഝഞടഠഡഢണതഥദധനപഫബഭമയരലവശഷസഹാഇീുൂെേൈൊോൌ്"  // Malayalam
    )

    fun switchLanguageAsync(langCode: String) {
        currentLang = langCode
        if (dictionaries.containsKey(langCode)) return
        
        Thread {
            loadDictionary(langCode)
        }.start()
    }

    private fun loadDictionary(langCode: String) {
        val dict = HashMap<String, Long>()
        val pDict = HashMap<String, ArrayList<Pair<String, Long>>>()
        try {
            val fileName = "${langCode}_dict.txt"
            val inputStream = context.assets.open(fileName)
            val reader = BufferedReader(InputStreamReader(inputStream))
            reader.forEachLine { line ->
                val parts = line.split(" ")
                if (parts.size >= 2) {
                    val word = parts[0].lowercase()
                    val freq = parts[1].toLongOrNull() ?: 1L
                    dict[word] = freq
                    
                    if (langCode == "en") {
                        val pKey = toPhoneticKey(word)
                        if (pKey.isNotEmpty()) {
                            val list = pDict.getOrPut(pKey) { ArrayList() }
                            list.add(Pair(word, freq))
                        }
                    }
                }
            }
            reader.close()
            // Corruption guard: hi_dict.txt (128 bytes) and kn_dict.txt (28 bytes)
            // are truncated stubs, not real dictionaries. Storing their mojibake
            // would let autocorrect "fix" correct words into garbage. Anything
            // under MIN_DICT_WORDS is treated as missing — we still cache the
            // (empty) entry so we don't re-parse the stub on every switch, and
            // correct() returns words unchanged for empty dictionaries.
            if (dict.size >= MIN_DICT_WORDS) {
                dictionaries[langCode] = dict
                phoneticDictionaries[langCode] = pDict
                Log.i("SpellCorrector", "Loaded $fileName with ${dict.size} words and ${pDict.size} phonetic keys.")
            } else {
                dictionaries[langCode] = HashMap()
                phoneticDictionaries[langCode] = HashMap()
                Log.w("SpellCorrector", "$fileName looks truncated/corrupt (${dict.size} entries) — autocorrect disabled for '$langCode'.")
            }
        } catch (e: Exception) {
            Log.w("SpellCorrector", "Dictionary $langCode not found. Skipping autocorrect for this language.")
        }
    }

    /**
     * Compute robust consonant-skeleton phonetic key (Soundex / Double-Metaphone inspired)
     * Handles English transliterations from Indic speech accurately.
     */
    fun toPhoneticKey(input: String): String {
        if (input.isEmpty()) return ""
        var s = input.lowercase()

        // 1. Normalize common phonetic transliteration clusters
        s = s.replace("ph", "f")
            .replace("gh", "g")
            .replace("kh", "k")
            .replace("sh", "s")
            .replace("ch", "s")
            .replace("zh", "s")
            .replace("jh", "j")
            .replace("z", "j")
            .replace("w", "v")
            .replace("c", "k")
            .replace("q", "k")
            .replace("x", "ks")

        // 2. Collapse double consonants
        val sb = StringBuilder()
        var prevChar: Char? = null
        for (c in s) {
            if (c != prevChar) {
                sb.append(c)
                prevChar = c
            }
        }
        s = sb.toString()

        // 3. Remove vowels except leading indicator
        val firstChar = s.first()
        val remaining = s.substring(1).filter { it !in "aeiouy" }
        val lead = if (firstChar in "aeiouy") "*" else firstChar.toString()
        return lead + remaining
    }

    private fun levenshteinDistance(s1: String, s2: String): Int {
        val dp = Array(s1.length + 1) { IntArray(s2.length + 1) }
        for (i in 0..s1.length) dp[i][0] = i
        for (j in 0..s2.length) dp[0][j] = j
        for (i in 1..s1.length) {
            for (j in 1..s2.length) {
                val cost = if (s1[i - 1] == s2[j - 1]) 0 else 1
                dp[i][j] = minOf(
                    dp[i - 1][j] + 1,
                    dp[i][j - 1] + 1,
                    dp[i - 1][j - 1] + cost
                )
            }
        }
        return dp[s1.length][s2.length]
    }

    private fun edits1(word: String, alphabet: String): Set<String> {
        val edits = mutableSetOf<String>()
        val splits = (0..word.length).map { Pair(word.substring(0, it), word.substring(it)) }

        // Deletes
        splits.forEach { if (it.second.isNotEmpty()) edits.add(it.first + it.second.substring(1)) }
        // Transposes
        splits.forEach { if (it.second.length > 1) edits.add(it.first + it.second[1] + it.second[0] + it.second.substring(2)) }
        // Replaces
        splits.forEach { split ->
            if (split.second.isNotEmpty()) {
                alphabet.forEach { char -> edits.add(split.first + char + split.second.substring(1)) }
            }
        }
        // Inserts
        splits.forEach { split ->
            alphabet.forEach { char -> edits.add(split.first + char + split.second) }
        }
        return edits
    }

    fun correct(word: String): String {
        // Skip purely numeric words, punctuation, or empty strings
        if (word.isBlank() || word.matches(Regex("[0-9\\p{Punct}]+"))) return word
        
        // Skip ALL-CAPS words as they are usually acronyms (like KLE, ISRO, NASA)
        if (word.matches(Regex("^[A-Z]+$"))) return word
        
        val dict = dictionaries[currentLang] ?: return word
        if (dict.isEmpty()) return word

        val lowerWord = word.lowercase()
        
        // 1. If it's already a valid high-frequency dictionary word, trust it
        if (dict.containsKey(lowerWord) && (dict[lowerWord] ?: 0L) > 10L) {
            return word
        }

        // 2. Phonetic Skeleton matching (ultra-accurate for Indic transliterations)
        val pDict = phoneticDictionaries[currentLang]
        if (pDict != null && pDict.isNotEmpty()) {
            val pKey = toPhoneticKey(lowerWord)
            val candidates = pDict[pKey]
            if (!candidates.isNullOrEmpty()) {
                // Rank candidates by lowest Levenshtein distance and highest corpus frequency
                val best = candidates.minByOrNull { (candWord, freq) ->
                    val dist = levenshteinDistance(lowerWord, candWord)
                    // Heavily penalize distance, reward frequency
                    dist * 1000.0 - Math.log(freq.toDouble().coerceAtLeast(1.0))
                }
                if (best != null) {
                    val candWord = best.first
                    return if (word.first().isUpperCase()) {
                        candWord.replaceFirstChar { it.uppercase() }
                    } else {
                        candWord
                    }
                }
            }
        }

        // 3. SymSpell Edit-Distance-1 fallback
        val alphabet = alphabets[currentLang] ?: alphabets["en"]!!
        val e1 = edits1(lowerWord, alphabet)
        val knownE1 = e1.filter { dict.containsKey(it) }
        if (knownE1.isNotEmpty()) {
            val bestCorrection = knownE1.maxByOrNull { dict[it]!! } ?: return word
            return if (word.first().isUpperCase()) {
                bestCorrection.replaceFirstChar { it.uppercase() }
            } else {
                bestCorrection
            }
        }

        return word
    }
}
