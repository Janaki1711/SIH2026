# Offline STT CER Benchmark — Approach C gate (2026-09-24)

*(re-issued after /tmp wipe; original run 2026-09-24 pre-restart)*

Method: gTTS-synthesized references → 16 kHz mono PCM → CER (space-insensitive
edit distance). Baseline = current in-APK AI4Bharat encoder (`encoder.onnx` +
`ctcGreedyDecode` + `convertIndicScript`, replicated by `lab2.py`). Same audio
fed to all contenders. Runtime: laptop CPU, faster-whisper/CTranslate2 int8.

## Contenders

| model | size (int8) | source |
|---|---|---|
| current AI4Bharat encoder (in APK) | 197 MB (fp32 onnx) | APK assets |
| parambharat/whisper-tiny-south-indic | **41 MB** | CT2 int8 (verified) |
| steja/whisper-small-marathi | ~240 MB (int8 est.) | CT2 fp32 = 923 MB |
| openai/whisper-{tiny,base,small} vanilla | 39/81/237 MB | HF |
| ai4bharat/indic-whisper-* | — | **DOES NOT EXIST** (401; handoff IDs wrong) |
| Harveenchadha/vakyansh-wav2vec2-* (per-lang) | untested | HF (hindi-4200h … malayalam-8h) |

## Results (CER, lower = better)

### Telugu (te) — phone A spinner language
| sample | current (+conv) | tiny-south-indic (beam10 + `initial_prompt=తెలుగు`) |
|---|---|---|
| greet | 0.17 | 0.12 |
| help | 0.30 | 0.06 |
| te_fire (long) | 0.31 | 0.07–0.12 |
| te_loc (numbers) | 0.31 | 1.00 **without** prompt → **0.26 with** prompt |
| te_short | 0.28 | 0.20 |

**Winner: tiny-south-indic on every Telugu sample.** Model collapses to
`நா`/`.` on some inputs without prompt → ALWAYS pass target-language
`initial_prompt` + output-length-vs-duration sanity check + conformer fallback.

### Tamil / Kannada / Malayalam — current encoder's weakest languages
| sample | current (+conv) | tiny-south-indic |
|---|---|---|
| ta_help | 0.61 | **0.05** |
| kn_help | 0.45 | **0.31** |
| ml_help | 0.51 | **0.34** |

**Winner: tiny-south-indic on all three.**

### Marathi (mr) — phone Nupur's language
| sample | current | steja-small | tiny-south-indic | openai-small |
|---|---|---|---|---|
| mr_fire | 0.35 | **0.11** | ~1.0 garbage | 0.32 |
| mr_help | 0.09 | 0.11 | ~1.3 | 0.11 |
| mr_greet | 0.40 | **0.10** | ~1.0 | 0.40 |

steja wins but int8 ≈ 240 MB exceeds budget; no tiny general mr fine-tune
exists. Vanilla whisper-small **hallucinates on Telugu** (CER ~1.0, 25 s
runaway) ⇒ no single vanilla model. **Keep current encoder for mr.**

### Hindi / Gujarati / Punjabi / Bengali — current encoder holds
hi **0.03**, gu **0.13**, pa 0.30, bn 0.33 (steja on hi = 0.24, worse).
**Keep current encoder for hi/bn/pa/gu/or/mr.**

## Decision (gate: integrate ONLY winner)

**PASS — integrate `parambharat/whisper-tiny-south-indic` (41 MB) for
te/ta/kn/ml ONLY.** Strict improvement, zero regressions:

- APK: 244 − 23 (drop dead `ctc_decoder.onnx`) + ~41 ≈ **262 MB ≤ 300 cap**.
- hi/bn/pa/gu/or/mr → current encoder unchanged.
- mr gain not size-feasible today → approach B (Google STT / offline pack).

## Integration contract
1. Runtime: **whisper.cpp** (ggml q8_0 ≈ 41 MB; NEON-optimized; built-in
   tokenizer/mel/language+prompt support; FetchContent in existing CMake —
   protobuf precedent exists).
2. Language gate in `MainActivity`: spinner ∈ {te,ta,kn,ml} → whisper path,
   else existing native path. en-IN detector leg unchanged.
3. Collapse guard: target-language prompt + min-output-chars/duration check →
   fallback to current encoder transcript.
4. Re-run gate with the SHIPPED decoder (whisper.cpp greedy, not faster-whisper
   beam) on the 12 samples before integrating — see `refs.json`.
5. `txLangForScript` / `convertIndicScript` untouched (whisper emits native
   script already).

## Repro assets (this dir)
- `refs.json` — 12 sample references + languages
- `<name>.raw` — 16 kHz mono PCM test utterances
- `lab2.py` family — current-encoder baselines (see session history)
- venv: `/tmp/opencode/onnxenv`
- HF cache (survived wipe): `~/.cache/huggingface/hub/models--parambharat--…`

---

# On-device verification (2026-09-24, phone 3353f694 / CPH2613, SM7550, 8 cores)

Integration build: whisper.cpp `d09f61a` via FetchContent, ggml q8_0
(43,537,433 B) in assets, greedy `best_of=1`, `temperature_inc=0`,
`no_timestamps`, `no_context=true`, per-lang initial prompt, forced `-l`,
`n_threads=4`. Dead `ctc_decoder.onnx` (23 MB) dropped — encoder emits direct
log_probs. APK **270 MB ≤ 300 cap**.

Driven without a human on the mic via the intent hook
(`MainActivity --es stt_test_wav <file> --es stt_test_lang <lang>` →
`startAudioCapture → pushAudioPCM → stopAudioCaptureAndTranscribe`):

| sample | path | audio | infer | transcript vs reference |
|---|---|---|---|---|
| te_fire | whisper | 5.0 s | 2.9 s | ✅ correct (CER ~0.07) |
| te_loc | whisper | 3.3 s | 2.1 s | ✅ CER ~0.29 (matches laptop gate) |
| te_short | whisper | 2.0 s | 1.3 s | ✅ CER ~0.13 |
| ta_help | whisper | 4.1 s | 2.3 s | ✅ near-perfect |
| kn_help | whisper | 4.4 s | 1.5 s | ✅ near-perfect |
| ml_help | whisper | 3.0 s | 1.9 s | ✅ good |
| greet | whisper | 3.4 s | 3.6 s | ✅ Telugu script (conformer used to flip to Tamil) |
| help | whisper | 3.8 s | 1.9 s | ✅ |
| hi_help | conformer | 3.5 s | 0.5 s | ✅ perfect — fallback intact |
| mr_fire | conformer | 2.4 s | 0.4 s | ✅ fallback intact (mr known-weak, approach B later) |

Notes:
- `inferMs` includes the ~0.25 s lazy model load (every run was a fresh
  process via `am force-stop`); steady-state decode is faster.
- **Critical build fix:** AGP builds the debug variant at `CMAKE_BUILD_TYPE=Debug`
  = `-O0`, which made the first on-device run take **45.5 s** for 5 s of audio.
  Forcing `-O2` on `whisper ggml ggml-base ggml-cpu audio_stt_core` brought it
  to **4.4 s** (10×). Any future perf regression here: check build type first.
- Ship config must stay bit-for-bit with the laptop gate: greedy, `best_of=1`,
  `temperature_inc=0`, `-nt`, per-lang prompt, forced language, 4 threads.
