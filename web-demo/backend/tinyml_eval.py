# tinyml_eval.py
"""
iTantra M3 — Comprehensive TinyML & Hybrid Semantic Engine Evaluation Script
Evaluates:
1. TinyML Role Classification Metrics (Precision, Recall, F1, Accuracy) on strict unseen test set
2. Model Size and Average CPU Inference Latency
3. End-to-End Semantic Extraction and Meaning Preservation on the 5 Core + 6 Extended Test Cases
4. Packet Encoding, Compression, Decompression, and Language Realization
"""

import os
import sys
import io
import time
import json
from sklearn.metrics import classification_report, accuracy_score, f1_score

# Ensure utf-8 stdout for multilingual test strings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import semantic_parser
import semantic_compressor
import translation_engine
from tinyml_dataset import build_dataset, ID2ROLE
from tinyml_classifier import TinyMLClassifier, MODEL_FILE


def run_evaluation():
    print("=" * 70)
    print("iTANTRA M3 — TINYML & HYBRID SEMANTIC EVALUATION REPORT")
    print("=" * 70)

    # 1. Model Artifact Size
    clf = TinyMLClassifier.get_instance()
    size_bytes = os.path.getsize(MODEL_FILE) if os.path.exists(MODEL_FILE) else 0
    size_kb = size_bytes / 1024.0
    size_mb = size_bytes / (1024.0 * 1024.0)
    print(f"\n[1] MODEL ARTIFACT SIZE")
    print(f"    Path: {MODEL_FILE}")
    print(f"    Size: {size_kb:.1f} KB ({size_mb:.3f} MB) — [Target: < 10 MB]")

    # 2. Strict Unseen Test Set Evaluation
    print(f"\n[2] STRICT UNSEEN TEST SET EVALUATION")
    _, test_data = build_dataset(num_train=1000, num_test=600, seed=123)
    y_true = [s["role_id"] for s in test_data]
    y_true_names = [ID2ROLE[i] for i in y_true]
    y_pred = []

    t_start = time.perf_counter()
    for s in test_data:
        role, conf = clf.predict_role(span=s["span"], left_ctx=s["left_ctx"], right_ctx=s["right_ctx"], full_text=s["text"])
        y_pred.append(role)
    total_time = time.perf_counter() - t_start
    avg_latency_ms = (total_time / len(test_data)) * 1000.0

    acc = accuracy_score(y_true_names, y_pred)
    macro_f1 = f1_score(y_true_names, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true_names, y_pred, average="weighted", zero_division=0)

    print(f"    Test Samples: {len(test_data)}")
    print(f"    Accuracy:     {acc * 100:.2f}%")
    print(f"    Macro F1:     {macro_f1 * 100:.2f}%")
    print(f"    Weighted F1:  {weighted_f1 * 100:.2f}%")
    print(f"    Avg Latency:  {avg_latency_ms:.3f} ms / sample (CPU)")

    # 3. End-to-End Test Suite
    print(f"\n[3] END-TO-END HYBRID EVALUATION SUITE (5 Core + 6 Extended)")
    
    test_cases = [
        # --- 5 Core Test Cases ---
        ("CORE 1", "Send three rescue workers to Green Valley Hospital immediately; two people are injured and one is unconscious.", "en"),
        ("CORE 2", "Team Alpha 12 is moving east toward the old railway bridge, but the area is unsafe and the signal is weak.", "en"),
        ("CORE 3", "Everyone is terrified after the building collapsed near Nagpur; we need an ambulance and a medical team right now.", "en"),
        ("CORE 4", "पाँच लोग नदी के पास फंसे हुए हैं, तुरंत बचाव दल भेजें और क्षेत्र को सुरक्षित करें।", "hi"),
        ("CORE 5", "தீ விபத்து ஏற்பட்டுள்ளது, இரண்டு பேர் காயமடைந்துள்ளனர், உடனடியாக மருத்துவ உதவியை அனுப்புங்கள்.", "ta"),
        # --- 6 Extended Test Cases ---
        ("EXT 1", "Send help to Xyzgarh immediately.", "en"),
        ("EXT 2", "Sector 47 is unsafe.", "en"),
        ("EXT 3", "Unit Alpha 7 is requesting medical support.", "en"),
        ("EXT 4", "Seven people are trapped near the river.", "en"),
        ("EXT 5", "Team Alpha 7 is moving toward Sector 4.", "en"),
        ("EXT 6", "Everyone is frightened but the communication link is active.", "en"),
    ]

    all_passed = True
    for tag, text, lang in test_cases:
        t0 = time.perf_counter()
        msg = semantic_parser.parse(text, lang)
        parse_ms = (time.perf_counter() - t0) * 1000.0

        # Encode packet
        pkt_bytes = semantic_compressor.compress(msg)
        # Decode packet
        dec_msg = semantic_compressor.decompress(pkt_bytes)
        # Realize
        realized = translation_engine.realize(dec_msg, lang)

        fields_dict = {f["field"]: f"{f['value']} [{f.get('source', 'RULE')}]" for f in dec_msg.to_dict()["fields"]}
        is_semantic = not dec_msg.is_fallback

        print(f"\n  ------------------------------------------------------------")
        print(f"  [{tag}] Input ({lang}): \"{text}\"")
        print(f"  Status: {'SEMANTIC (OK)' if is_semantic else 'FALLBACK (FAIL)'} | Packet Size: {len(pkt_bytes)} bytes | Parse Latency: {parse_ms:.2f} ms")
        print(f"  Extracted Fields: {fields_dict}")
        print(f"  Reconstructed ({lang}): \"{realized}\"")

        if not is_semantic:
            all_passed = False

    print("\n" + "=" * 70)
    print(f"FINAL RESULT: {'ALL TEST CASES PASSED' if all_passed else 'SOME CASES FAILED'}")
    print("=" * 70)
    return acc, macro_f1, avg_latency_ms, size_kb


if __name__ == "__main__":
    run_evaluation()
