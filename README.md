# Bharat AI — Zero-Leak Examination Management System

> **Cloud-native, AI-powered, zero-trust examination distribution architecture for high-stakes national and state examinations.**

---

## 🎯 Core Principle

> **"The complete readable examination paper must not exist anywhere before the authorized examination release time."**

Everything in this project — every design decision, every protocol, every line of code — traces back to this single sentence. **Do not just protect the final paper; eliminate its pre-exam existence.**

### End-to-End Flow
```
[ Generate ] ➔ [ Encrypt ] ➔ [ Time-lock ] ➔ [ Authorize ] ➔ [ Decrypt ] ➔ [ Print ] ➔ [ Audit ]
```

---

## 🚨 The Problem

Exam paper leaks happen because a fully readable paper exists in some form — a physical file, a leak from a printer, an insecure staging server, or a photo taken of a printout — hours or days before the exam starts. This vulnerable time window is where virtually every leak originates.

**Bharat AI eliminates this window entirely:**
- The paper is assembled and encrypted centrally under multi-party human authorization.
- The decryption key is locked on the server and only released at the exact authorized release time to authenticated centres.
- The examination paper is only decrypted in memory at the edge examination centre moments before printing.
- Every single action, request, authorization, and decryption is recorded in an immutable, tamper-evident hash-chain audit log.
- Every printed physical copy contains unique forensic watermarking (QR / micro-serial) mapping back to the exact centre, candidate room, and timestamp.

---

## 🏛️ Target Architecture vs. Prototype Scope

### Full Target Architecture (Production Vision)

1. **Tier 1 — Central AI Engine**: Encrypted question bank $\rightarrow$ AI-assisted selection & Bloom's taxonomy difficulty balancing (human-in-the-loop approval) $\rightarrow$ automated paper assembly $\rightarrow$ SHA-256 signing $\rightarrow$ AES-256-GCM encryption.
2. **Tier 2 — Cloud Infrastructure**: High-availability cloud infrastructure with zero-trust networking and hardware-level isolation.
3. **Tier 3 — Kubernetes Orchestration**: Containerized microservices (`auth`, `paper`, `crypto`, `time-lock`, `centre-mgmt`, `audit`, `key-release`), Calico CNI, zero-trust micro-segmentation, Prometheus/Grafana observability.
4. **Tier 4 — Edge Examination Centre**: Mutual TLS (mTLS) with hardware root of trust (HSM/biometrics) $\rightarrow$ time-locked key release verification $\rightarrow$ in-memory decryption $\rightarrow$ automated verified quota printing with forensic watermarks.

### Prototype Scope (10-Day Hackathon Implementation)

| Architecture Tier | Production Vision | 10-Day Prototype Scope |
| :--- | :--- | :--- |
| **Cloud Infrastructure** | Multi-region OpenStack / Cloud | **Terraform**-provisioned cloud infrastructure (AWS/GCP Free Tier or local libvirt) |
| **Orchestration** | Full multi-node K8s Cluster | **k3s / Docker Compose** (lightweight, real Kubernetes manifests & self-healing) |
| **Centre Hardware Auth** | HSM / Biometric hardware | **Mutual TLS (mTLS) with self-signed CA** + Scoped JWT RBAC |
| **Physical Separation** | Data Centre $\leftrightarrow$ Edge Centres | **Two physical devices** (Authority Host $\leftrightarrow$ Edge Laptop/Raspberry Pi) |
| **Paper Delivery** | Secure Print Network | In-memory decryption $\rightarrow$ **ReportLab/FPDF watermarked PDF** |

---

## 🌟 The Two Headline Differentiators

### 1. Hash-Chained, Tamper-Evident Audit Log
Every audit event stores:
$$\text{Current Hash} = \text{SHA-256}(\text{Previous Hash} + \text{Timestamp} + \text{Actor} + \text{Action} + \text{Payload Digest})$$
- A standalone verification CLI (`python -m audit_service.verify`) recomputes the chain.
- **Live Hackathon Demo:** Manually modify a row in the audit database; the verification tool flags the exact broken block and timestamp immediately.

### 2. Forensic Per-Copy Watermarking & Leak Traceability
- Every printed copy is injected with a cryptographically signed, steganographic / QR watermark encoding:
  - Centre ID
  - Room / Candidate ID
  - Print Timestamp & Batch Sequence
- If an unauthorized photo or paper leak occurs post-printing, the physical leak is forensically traceable to the exact centre, room, and minute.

---

## 👥 Team & Ownership

| Person | Team Member | Vertical Slice Ownership | Key Deliverables |
| :--- | :--- | :--- | :--- |
| **Person 1** | **Nupur** | **Question Bank + AI Selection Engine** (Tier 1 Front-Half) | Question schema, embedding duplicate detection, difficulty balancing, human-in-the-loop approval endpoint |
| **Person 2** | **Parth** | **Crypto Core + Zero-Trust Auth** | AES-256-GCM + SHA-256 signing, OpenSSL PKI / mTLS, Scoped JWT auth, adversarial security testing |
| **Person 3** | **Janaki** | **Backend Services + IaC** (Tiers 2 & 3) | FastAPI microservices, Docker Compose, k3s manifests, Terraform IaC, rate-limiting & resilience |
| **Person 4** | **Vaibhav** | **Edge Centre Client + Physical Demo** | Edge polling client, in-memory decryption, per-copy dynamic PDF watermarking, dual-device setup |
| **Person 5** | **Chhavi** | **Audit Trail + Hash-Chain** | Hash-chain engine, API audit middleware hooks, standalone audit verification CLI, tamper demo |
| **Person 6** | **Vaibhav** | **Dashboard + Integration + Documentation** | Live WebSocket monitoring dashboard, daily end-to-end integration runs, SIH presentation / PPT & report |

---

## 🛠️ Technology Stack

- **Backend & APIs:** Python 3.11+, FastAPI, Uvicorn, Pydantic
- **Cryptography & Security:** Python `cryptography` (AES-256-GCM, SHA-256), OpenSSL (mTLS / X.509 certs), PyJWT
- **AI & NLP:** `sentence-transformers` / LLM API (embedding deduplication, Bloom's taxonomy tagging)
- **Infrastructure & Containers:** Docker, Docker Compose, k3s (Lightweight Kubernetes), Terraform
- **Database & Storage:** SQLite / MongoDB (Encrypted storage)
- **Edge Document Generation:** ReportLab, PyPDF, qrcode
- **Monitoring & Dashboard:** Streamlit / React + Tailwind, WebSockets, Prometheus, Grafana

---

## 📅 10-Day Execution Timeline

- **Days 1–3:** Core module construction against API stubs; first end-to-end loop running by Day 3.
- **Days 4–6:** Integration across real network (2 physical devices), implement hash-chain & watermarking.
- **Days 6–7:** k3s orchestration & Terraform IaC provisioning scripts.
- **Days 7–8:** Adversarial testing & tamper simulation (breaking our own system and documenting defense).
- **Day 9:** SIH final report, presentation slides, 2 full rehearsal dry-runs.
- **Day 10:** Buffer day — backup video recording & live demo rehearsal (no new code).

---

## 🎬 90-Second Demo Script

1. **Encrypted State:** Show the encrypted package on the edge centre device. Attempt to read or decrypt it before scheduled time $\rightarrow$ strictly rejected.
2. **Time Trigger:** Advance the time-lock window to the authorized release minute.
3. **Key Release & Auth:** Edge centre authenticates via mTLS + JWT. The Central Authority verifies credentials and releases the decryption key.
4. **Edge In-Memory Decrypt:** The client decrypts the paper in memory (no plaintext written to disk).
5. **Traceable Printing:** PDF generates with dynamic per-copy QR/watermarking. Show two distinct generated copies.
6. **Immutable Audit:** Open the real-time dashboard showing every event logged in the cryptographic hash chain. Run the verification CLI to prove zero tampering.

---

## 📂 Repository Structure

```
SIH2026/
├── README.md                          # Project Master Overview
├── TEAM_ROADMAP.md                    # Detailed 10-Day Breakdown & Checklists
├── docker-compose.yml                 # Local multi-service orchestration
├── services/
│   ├── question_engine/               # Person 1 (Nupur)
│   ├── crypto_core/                   # Person 2 (Parth)
│   ├── backend/                       # Person 3 (Janaki)
│   ├── edge_client/                   # Person 4 (Vaibhav)
│   ├── audit_service/                 # Person 5 (Chhavi)
│   └── dashboard/                     # Person 6 (Vaibhav)
├── infra/
│   ├── terraform/                     # Terraform IaC configurations
│   └── k3s/                           # Kubernetes deployment manifests
└── docs/                              # SIH Report, Architecture Diagrams, Presentation
```
