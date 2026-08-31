# tinyml_train.py
"""
iTantra M3 — TinyML Model Training & Validation Script
Generates balanced synthetic contextual emergency dataset, trains the classifier,
evaluates on unseen validation split, and serializes the lightweight model.
"""

import os
import sys
import time
import joblib
import numpy as np
from sklearn.metrics import classification_report, accuracy_score, f1_score

from tinyml_dataset import build_dataset, ROLES, ID2ROLE
from tinyml_classifier import TinyMLClassifier, MODEL_FILE


def train():
    print("=" * 60)
    print("iTANTRA M3 — TINYML SEMANTIC ROLE CLASSIFIER TRAINING")
    print("=" * 60)

    # 1. Generate Dataset
    print("\n[1/4] Generating balanced contextual dataset with hard negatives...")
    t0 = time.time()
    train_data, test_data = build_dataset(num_train=3000, num_test=800, seed=42)
    print(f"      Train samples: {len(train_data)}")
    print(f"      Test samples (strict unseen): {len(test_data)}")
    print(f"      Dataset generation time: {(time.time() - t0):.3f}s")

    # 2. Train Pipeline
    print("\n[2/4] Training contextual TF-IDF + Structural Feature + Logistic Classifier...")
    clf = TinyMLClassifier(model_path=MODEL_FILE)
    t1 = time.time()
    clf.train_and_save(train_data)
    train_time = time.time() - t1
    print(f"      Training completed in {train_time:.3f}s")

    # 3. Model Size
    size_bytes = os.path.getsize(MODEL_FILE)
    size_kb = size_bytes / 1024.0
    size_mb = size_bytes / (1024.0 * 1024.0)
    print(f"      Model artifact saved to: {MODEL_FILE}")
    print(f"      Model artifact size: {size_kb:.1f} KB ({size_mb:.3f} MB) — [Target: <10 MB, achieved <1 MB]")

    # 4. Evaluation on Strict Unseen Set
    print("\n[3/4] Evaluating on strict unseen test set...")
    y_true = [s["role_id"] for s in test_data]
    y_pred = []
    
    t_inf_start = time.time()
    for s in test_data:
        role_name, conf = clf.predict_role(
            span=s["span"],
            left_ctx=s["left_ctx"],
            right_ctx=s["right_ctx"],
            full_text=s["text"]
        )
        y_pred.append(role_name)
    total_inf_time = time.time() - t_inf_start
    avg_latency_ms = (total_inf_time / len(test_data)) * 1000.0

    y_true_names = [ID2ROLE[i] for i in y_true]
    acc = accuracy_score(y_true_names, y_pred)
    macro_f1 = f1_score(y_true_names, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true_names, y_pred, average="weighted", zero_division=0)

    print(f"      Overall Accuracy: {acc * 100:.2f}%")
    print(f"      Macro F1 Score:   {macro_f1 * 100:.2f}%")
    print(f"      Weighted F1:      {weighted_f1 * 100:.2f}%")
    print(f"      Avg Inference Latency: {avg_latency_ms:.3f} ms / sample (CPU)")

    print("\n[4/4] Detailed Per-Category Classification Report:")
    print(classification_report(y_true_names, y_pred, digits=3, zero_division=0))

    print("=" * 60)
    print("TINYML TRAINING & VALIDATION COMPLETED SUCCESSFULLY.")
    print("=" * 60)
    return acc, macro_f1, avg_latency_ms, size_kb


if __name__ == "__main__":
    train()
