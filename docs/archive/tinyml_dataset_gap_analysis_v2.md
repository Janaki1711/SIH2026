# iTANTRA M3 — V2 Dataset Gap Analysis & Compatibility Report

## EXECUTIVE SUMMARY

**RECOMMENDATION: DO NOT PROCEED WITH V2 INTEGRATION**

The `tinyml_hard_negative_v2.jsonl` dataset contains **label incompatibilities** with the existing frozen semantic baseline that prevent safe integration without modifying the core semantic layer.

---

## BASELINE CHARACTERISTICS

| Metric | Value |
|--------|-------|
| Training samples | 3,036 |
| Strict unseen test samples | 836 |
| Semantic roles | 10 |
| Role list | CALLSIGN, LOCATION, QUANTITY, RESOURCE, HAZARD, STATUS, EMOTION, CONDITION, ACTION, DIRECTION |
| Model size | 266.9 KB |
| Accuracy (baseline) | 98.27% |
| Macro F1 (baseline) | 98.38% |
| Avg latency | 1.668 ms |
| Architecture | Frozen (Character-WB TF-IDF + Word Context TF-IDF + Structural Features + L2 Logistic Regression) |

---

## V2 DATASET CHARACTERISTICS

| Metric | Value |
|--------|-------|
| Total records | 2,681 |
| Valid records (after removing malformed) | 2,594 |
| Invalid records (empty spans) | 87 |
| Exact duplicates with baseline | 0 |
| Test set leakage | 0 |
| Languages | English (90.4%), Hindi, Marathi, Tamil, Telugu, Kannada, Code-mixed |

### V2 Label Distribution

| Label | Count | % | Compatible |
|-------|-------|---|------------|
| LOCATION | 1,067 | 41.1% | ✓ Yes |
| QUANTITY | 817 | 31.5% | ✓ Yes |
| CALLSIGN | 607 | 23.4% | ✓ Yes |
| **IDENTIFIER** | **532** | **20.5%** | **✗ NO** |
| CONDITION | 431 | 16.6% | ✓ Yes |
| RESOURCE | 427 | 16.5% | ✓ Yes |
| DIRECTION | 320 | 12.3% | ✓ Yes |
| **ORGANIZATION** | **209** | **8.1%** | **✗ NO** |
| HAZARD | 141 | 5.4% | ✓ Yes |
| **EVENT** | **65** | **2.5%** | **✗ NO** |
| STATUS | 8 | 0.3% | ✓ Yes |

---

## CRITICAL INCOMPATIBILITIES

### 1. NEW LABELS NOT IN BASELINE (806 records / 31.1% of V2)

#### IDENTIFIER (532 records)
**Definition**: Infrastructure or system identifiers (e.g., "Unit 24", "Route 25", "Gate 12", "Checkpoint 89")

**Examples**:
- "Unit 24 is moving toward Route 25." → IDENTIFIER: "Unit 24", "Route 25"
- "Send five teams to Gate 12." → IDENTIFIER: "Gate 12"
- "Crew 88 is moving toward Checkpoint 89." → IDENTIFIER: "Crew 88", "Checkpoint 89"

**Problem**: These are **different** from CALLSIGN (team names like "Alpha 12") and LOCATION. They represent infrastructure identifiers not captured in baseline.

**Cannot safely map**: IDENTIFIER is a distinct semantic class.

---

#### ORGANIZATION (209 records)
**Definition**: Organizations and agencies (e.g., "Coast Guard", "Fire Department", "NDRF")

**Examples**:
- "Casualties from Sundapur are being sent to Coast Guard."
- "District Administration has dispatched a team to Kaldora."
- "Contact Fire Department regarding the situation at Ghoripada."

**Problem**: Organizations are semantic entities distinct from RESOURCE. Fire truck = RESOURCE; Fire Department = ORGANIZATION.

**Cannot safely map**: ORGANIZATION is semantically different from RESOURCE.

---

#### EVENT (65 records)
**Definition**: Events or incident descriptions (e.g., "The building collapsed", "A landslide occurred")

**Examples**:
- "The building collapsed near Castellan Ridge." → EVENT: "The building collapsed"
- "A landslide occurred near Karvenagar Station." → EVENT: "A landslide occurred"
- "An explosion occurred near Ghoripada." → EVENT: "An explosion occurred"

**Problem**: EVENT describes incident as event phrase, different from HAZARD which is a condition state.

**Cannot safely map**: EVENT (what happened) ≠ HAZARD (danger condition).

---

### 2. MISSING BASELINE COVERAGE

| Role | V2 Count | Status |
|------|----------|--------|
| ACTION | 0 | **NOT COVERED** |
| EMOTION | 0 | **NOT COVERED** |

V2 dataset omits ACTION ("send", "dispatch", "moving") and EMOTION ("terrified", "scared") roles entirely.

---

## DATA QUALITY ASSESSMENT

| Check | Result |
|-------|--------|
| JSON validity | ✓ PASS |
| Schema completeness | ⚠ WARNING (87 empty spans, 3.2%) |
| Span-text consistency | ✓ PASS |
| Duplicate with baseline | ✓ PASS |
| Test set leakage | ✓ PASS |

---

## LABEL COMPATIBILITY MATRIX

```
Baseline Role    | V2 Records | Status        | Notes
-----------------|-----------|---------------|------------------
CALLSIGN         | 607       | ✓ Compatible  | High quality
LOCATION         | 1,067     | ✓ Compatible  | Largest share
QUANTITY         | 817       | ✓ Compatible  | Good coverage
RESOURCE         | 427       | ✓ Compatible  | Adequate
HAZARD           | 141       | ✓ Compatible  | Lower coverage
STATUS           | 8         | ✓ Compatible  | Minimal
DIRECTION        | 320       | ✓ Compatible  | Good coverage
CONDITION        | 431       | ✓ Compatible  | Good coverage
ACTION           | 0         | ✗ NOT COVERED | Entirely absent
EMOTION          | 0         | ✗ NOT COVERED | Entirely absent
IDENTIFIER       | 532       | ✗ INCOMPATIBLE| New role
ORGANIZATION     | 209       | ✗ INCOMPATIBLE| New role
EVENT            | 65        | ✗ INCOMPATIBLE| New role
```

---

## SPECIFICATION COMPLIANCE

Per specification:

> "Do NOT silently rename semantic labels."
> "If labels are incompatible, report exactly which labels are incompatible and why."
> "and if compatibility requires a source change, STOP and report it instead of changing it."

**Current status**: Compliance requires STOP — incompatible labels require either remapping (violates "Do NOT silently rename") or semantic layer modification (violates frozen layer constraint).

---

## RECOMMENDATION

### **STOP INTEGRATION — DO NOT PROCEED**

**Reason**: V2 dataset contains semantic labels (IDENTIFIER, ORGANIZATION, EVENT) fundamentally incompatible with frozen baseline.

**Resolution**: V2 dataset author must re-annotate using 10-role baseline taxonomy with explicit sign-off from semantic layer owner.

---

**Report Date**: 2024
**Baseline Version**: iTantra M3 TinyML v1.0 (frozen semantic layer)
**Status**: INTEGRATION BLOCKED
