package org.isro.itantra.audio

import android.content.Context
import android.util.Log
import java.io.BufferedReader
import java.io.InputStreamReader

class SpellCorrector(private val context: Context) {
    // Cache for loaded language dictionaries
    private val dictionaries = HashMap<String, HashMap<String, Long>>()
    
    @Volatile
    private var currentLang: String = "en"

    // Alphabets for edits (insertions and replacements)
    private val alphabets = mapOf(
        "en" to "abcdefghijklmnopqrstuvwxyz",
        "hi" to "अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहृािीुूेैोौंः", // Devanagari (Hindi/Marathi)
        "mr" to "अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहृािीुूेैोौंः",
        "ta" to "அஆஇஈஉஊஎஏஐஒஓஔகஙசஞடணதநனபமயரறலளழவஷஸஹ்ாிீுூெேைொோௌ", // Tamil
        "te" to "అఆఇఈఉఊఋఎఏఐఒఓఔకఖగఘఙచఛజఝఞటఠడఢణతథదధనపఫబభమయరలవశషసహాిీుూెేైొోౌ్", // Telugu
        "bn" to "অআইঈউঊঋএঐওঔকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহািীুূেৈোৌ্", // Bengali
        "gu" to "અઆઇઈઉઊઋએઐઓઔકખગઘઙચછજઝઞટઠડઢણતથદધનપફબભમયરલવશષસહાિીુૂેૈોૌ્", // Gujarati
        "pa" to "ਅਆਇਈਉਊਏਐਓਔਕਖਗਘਙਚਛਜਝਞਟਠਡਢਣਤਥਦਧਨਪਫਬਭਮਯਰਲਵਸ਼ਸਹਾਿੀੁੂੇੈੋੌ੍", // Punjabi
        "kn" to "ಅಆಇಈಉಊಋಎಏಐಒಓಔಕಖಗಘಙಚಛಜಝಞಟಠಡಢಣತಥದಧನಪಫಬಭಮಯರಲವಶಷಸಹಾಿೀುೂೆೇೈೊೋೌ್", // Kannada
        "ml" to "അആഇഈഉഊഋഎഏഐഒഓഔകഖഗഘങചഛജഝഞടഠഡഢണതഥദധനപഫബഭമയരലവശഷസഹാിീുൂെേൈൊോൌ്"  // Malayalam
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
        try {
            val fileName = "${langCode}_dict.txt"
            val inputStream = context.assets.open(fileName)
            val reader = BufferedReader(InputStreamReader(inputStream))
            reader.forEachLine { line ->
                val parts = line.split(" ")
                if (parts.size >= 2) {
                    dict[parts[0]] = parts[1].toLongOrNull() ?: 1L
                }
            }
            reader.close()
            Log.i("SpellCorrector", "Loaded $fileName with ${dict.size} words.")
        } catch (e: Exception) {
            Log.w("SpellCorrector", "Dictionary $langCode not found. Skipping autocorrect for this language.")
        }
        dictionaries[langCode] = dict
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
        
        // Skip very short words (1-2 letters) to prevent them from turning into "a" or "i"
        if (word.length <= 2) return word
        
        // Skip ALL-CAPS words as they are usually acronyms (like KLE, ISRO, NASA)
        if (word.matches(Regex("^[A-Z]+$"))) return word
        
        val dict = dictionaries[currentLang] ?: return word
        if (dict.isEmpty()) return word // No file loaded for this lang
        
        val lowerWord = word.lowercase()
        // If it's already a valid word, trust it and return ORIGINAL case
        if (dict.containsKey(lowerWord)) return word

        val alphabet = alphabets[currentLang] ?: alphabets["en"]!!
        
        val e1 = edits1(lowerWord, alphabet)
        val knownE1 = e1.filter { dict.containsKey(it) }
        if (knownE1.isNotEmpty()) {
            val bestCorrection = knownE1.maxByOrNull { dict[it]!! } ?: return word
            
            // Preserve original capitalization if the first letter was capitalized
            return if (word.first().isUpperCase()) {
                bestCorrection.replaceFirstChar { it.uppercase() }
            } else {
                bestCorrection
            }
        }

        return word
    }
}
