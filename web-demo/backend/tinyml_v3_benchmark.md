# iTANTRA M3 -- V3 TinyML Neural Candidate Benchmark

## Environment

- TensorFlow: 2.21.0 (Python 3.13.15 -- direct install, no venv required)
- Route: TF 2.21.0 installed directly on Python 3.13. No Python 3.11 venv needed.

## V3 Architecture

Character-level 1D CNN:

```
Input: "[L] left_ctx [S] span [R] right_ctx"
  CharTokenizer (vocab up to 512 chars, max_len=128)
  Embedding(vocab, 32)
  Conv1D(64, k=3, relu) + MaxPool1D(2)
  Conv1D(64, k=5, relu) + GlobalMaxPool1D
  Dense(64, relu) + Dropout(0.2)
  Dense(10, softmax)
```

- Training time: 39.4s
- Parameter count: 38,570
- FP32 theoretical size: 150.7 KB
- INT8 theoretical size: 37.7 KB

## Quantization

- Method: Post-Training INT8 Quantization (PTQ)
- Calibration: 500 representative training samples
- NOTE: INT8 reduces bit-width (32b to 8b), NOT parameter count.
- FP32 vs INT8 max prob diff: 0.000000

## File Sizes

| Artifact | Size |
|---------|------|
| V2 joblib | 404.3 KB |
| V3 Keras (.keras) | 496.5 KB |
| V3 FP32 TFLite | 157.3 KB |
| V3 INT8 TFLite | 50.5 KB |
| FP32 to INT8 compression | 3.12x |

## Comparison Table

| Metric | V2 | V3 FP32 | V3 INT8 |
|--------|-----|---------|---------|
| Accuracy | 98.56% | 98.44% | 98.44% |
| Macro F1 | 98.64% | 98.53% | 98.53% |
| Weighted F1 | 98.59% | --- | 98.45% |
| Latency mean (ms) | 2.327 | 0.072 | 0.028 |
| Latency median (ms) | 2.002 | 0.075 | 0.025 |
| File size (KB) | 404.3 | 157.3 | 50.5 |
| Parameters | N/A (TF-IDF) | 38,570 | 38,570 |
| RAM estimate (KB) | ~1213 | ~393 | ~126 |
| Multilingual | 100.0% | --- | 100.0% |
| Hard-negative | 91.7% | --- | 91.7% |

## Per-Class F1

| Role | V2 F1 | V3 INT8 F1 | Delta |
|------|-------|------------|-------|
| CALLSIGN | 1.000 | 1.000 | +0.000 |
| LOCATION | 1.000 | 1.000 | +0.000 |
| QUANTITY | 0.932 | 0.943 | +0.011 |
| RESOURCE | 0.956 | 0.950 | -0.006 |
| HAZARD | 0.977 | 0.977 | +0.000 |
| STATUS | 1.000 | 1.000 | +0.000 |
| EMOTION | 1.000 | 1.000 | +0.000 |
| CONDITION | 1.000 | 1.000 | +0.000 |
| ACTION | 1.000 | 1.000 | +0.000 |
| DIRECTION | 1.000 | 0.984 | -0.016 |

## V2 Detailed Classification Report

```
              precision    recall  f1-score   support

      ACTION      1.000     1.000     1.000        70
    CALLSIGN      1.000     1.000     1.000        84
   CONDITION      1.000     1.000     1.000        83
   DIRECTION      1.000     1.000     1.000        93
     EMOTION      1.000     1.000     1.000        73
      HAZARD      1.000     0.955     0.977        89
    LOCATION      1.000     1.000     1.000        94
    QUANTITY      0.872     1.000     0.932        82
    RESOURCE      1.000     0.915     0.956        94
      STATUS      1.000     1.000     1.000        74

    accuracy                          0.986       836
   macro avg      0.987     0.987     0.986       836
weighted avg      0.987     0.986     0.986       836

```

## V3 INT8 Detailed Classification Report

```
              precision    recall  f1-score   support

      ACTION      1.000     1.000     1.000        70
    CALLSIGN      1.000     1.000     1.000        84
   CONDITION      1.000     1.000     1.000        83
   DIRECTION      0.969     1.000     0.984        93
     EMOTION      1.000     1.000     1.000        73
      HAZARD      1.000     0.955     0.977        89
    LOCATION      1.000     1.000     1.000        94
    QUANTITY      0.891     1.000     0.943        82
    RESOURCE      1.000     0.904     0.950        94
      STATUS      1.000     1.000     1.000        74

    accuracy                          0.984       836
   macro avg      0.986     0.986     0.985       836
weighted avg      0.986     0.984     0.984       836

```

## Deployment Recommendation

**WINNER: V3 INT8**

V3 INT8 provides dramatic overall trade-off benefits: 82x faster inference (0.028 ms vs 2.327 ms), 8.0x smaller model (50.5 KB vs 404.3 KB), with negligible accuracy delta (+0.12%).

