# Bharat AI — Zero-Leak Examination Management System

> **Cloud-native, AI-powered, zero-trust examination distribution architecture for high-stakes national and state examinations.**

---

## 🎯 Core Principle

> **"The complete readable examination paper must not exist anywhere before the authorized examination release time."**

Everything in this project traces back to this single sentence: **Do not just protect the final paper; eliminate its pre-exam existence.**

### End-to-End Flow
```
[ Generate ] ➔ [ Encrypt ] ➔ [ Time-lock ] ➔ [ Authorize ] ➔ [ Decrypt ] ➔ [ Print ] ➔ [ Audit ]
```

---

## 🚨 The Problem

Exam paper leaks happen because a fully readable paper exists in some form — a file, a physical printout, or a photo — hours or days before the exam begins. That window is where every leak originates.

**Bharat AI removes that window entirely:**
- The paper is assembled and encrypted centrally under human authorization.
- The decryption key is locked on the server and only released at the exact authorized release time to authenticated centres.
- The examination paper is only decrypted in memory at the edge centre moments before printing.
- Every single action is recorded in an immutable, tamper-evident hash-chain audit log.
- Every printed physical copy contains unique forensic watermarking (QR / micro-serial) mapping back to the exact centre, candidate room, and timestamp.

---

## 👥 Team Responsibilities & Work Allocation

---

### 1. Nupur — Question Bank & AI Selection Engine
**Focus:** Central AI Engine, Question Bank & Dynamic Assembly  
**Tools:** Python, SQLite / MongoDB, `sentence-transformers` / LLM API

- **Question Schema & Seeding:** Design comprehensive schema (`topic`, `subtopic`, `difficulty`, `marks`, `bloom_taxonomy`, `tags`, `last_used_year`, `embedding_vector`) and seed realistic question sets across subjects.
- **Paper Assembly Engine:** Develop `assemble_paper(subject, difficulty_distribution, total_marks)` to dynamically generate balanced exam sets.
- **AI Deduplication & Validation:** Implement embedding vector similarity matching against previous exam papers to detect duplicates or near-duplicates (> 0.85 cosine similarity).
- **Human-in-the-Loop Authorization:** Build human approval/rejection endpoints so AI assists selection while authorized officials give final approval.
- **Difficulty Balancing & Analytics:** Bloom's taxonomy weighted balancing and question bank coverage gap analytics.
- **Handoff:** Standardized paper JSON structure passed to crypto and backend services.

---

### 2. Parth — Crypto Core & Zero-Trust Authentication
**Focus:** Cryptographic Engine, PKI Infrastructure & Authorization  
**Tools:** Python `cryptography` library, OpenSSL, `PyJWT`

- **Symmetric Encryption & Signing:** Implement `sign_and_encrypt(paper)` and `decrypt_and_verify(package, key)` using SHA-256 (integrity/signature) and AES-256-GCM (authenticated encryption).
- **Public Key Infrastructure & Mutual TLS (mTLS):** Build a self-signed Root CA, issue X.509 certificates to authority and edge centre nodes, and enforce bidirectional TLS encryption.
- **Scoped JWT Role-Based Access Control:** Granular token validation enforcing least privilege for `centre-role`, `authority-role`, and `invigilator-role`.
- **Adversarial Security Testing:** Test and defend against replay attacks, pre-release decryption attempts, forged JWTs, and tampered ciphertext packages.
- **Handoff:** Importable crypto/auth module and verified certificate authority configurations.

---

### 3. Janaki — Backend Microservices & Infrastructure as Code (IaC)
**Focus:** Microservice Architecture, Containerization & Cloud Infrastructure  
**Tools:** FastAPI, Uvicorn, Docker Compose, k3s, Terraform

- **FastAPI Microservices:** Design and scaffold modular backend services (`auth_service`, `paper_service`, `timelock_service`, `key_release_service`).
- **Core Pipeline Wiring:** Integrate question engine, crypto core, and audit hooks into a seamless end-to-end API lifecycle.
- **Container Orchestration (Docker & k3s):** Provide local multi-container `docker-compose.yml` and Kubernetes (`k3s`) manifests demonstrating pod self-healing and zero-trust networking.
- **Terraform Infrastructure as Code (IaC):** Write Terraform scripts (`main.tf`, `variables.tf`) to provision cloud nodes/VMs, enabling demoable `terraform apply` and `terraform destroy`.
- **Production Hardening:** Implement API rate limiting, retries, structured error handling, and health-check monitoring.
- **Handoff:** Stable, documented REST and WebSocket API endpoints.

---

### 4. Vaibhav — Edge Centre Client & Physical Demonstration
**Focus:** Edge Centre Deployment, In-Memory Decryption & Secure Printing  
**Tools:** Python, ReportLab / FPDF, QRCode, Physical Laptop / Raspberry Pi

- **Edge Client Lifecycle:** Walk full sequence: Authenticate (mTLS + JWT) $\rightarrow$ Poll release time $\rightarrow$ Request decryption key $\rightarrow$ In-memory decryption $\rightarrow$ Print buffer.
- **Dual-Device Physical Setup:** Run the edge client on a separate physical device on the local network (laptop or Raspberry Pi) making genuine network calls to the authority server.
- **Forensic Per-Copy Watermarking:** Generate dynamically watermarked PDFs where each copy contains a unique QR code and micro-serial tracking `Centre ID + Room + Candidate ID + Timestamp`.
- **Zero-Footprint Print Execution:** Ensure decrypted plaintext never persists to the client disk and is wiped immediately after generating the print stream.
- **Handoff:** Live edge client application, verified printing pipeline, and distinct physical print samples.

---

### 5. Chhavi — Immutable Audit Trail & Hash-Chain Engine
**Focus:** Tamper-Evident Logging & Standalone Verification  
**Tools:** Python, Hashlib, SQLite / MongoDB, WebSockets

- **Cryptographic Hash-Chain Ledger:** Implement the hash-chain algorithm where each entry records $\text{Hash} = \text{SHA-256}(\text{Previous Hash} + \text{Event Data})$.
- **Middleware Audit Hooks:** Instrument every backend microservice to record auth attempts, key queries, paper assembly, print requests, and unauthorized accesses.
- **Standalone Verification CLI:** Build an independent verification command-line tool that anyone (including evaluators) can run to mathematically audit the entire event ledger.
- **Live Tamper-Detection Demo:** Demonstrate live tampering resistance by altering a database row directly and showing how `verify_chain()` immediately flags the exact corrupted block.
- **Handoff:** Standalone audit verification utility and real-time event streaming interface.

---

### 6. Vaibhav — Real-Time Dashboard, Integration & Documentation
**Focus:** Live Monitoring Interface, Full-Pipeline Integration & SIH Deliverables  
**Tools:** Streamlit / React + Tailwind, WebSockets, Prometheus / Grafana, Canva / PowerPoint

- **Real-Time Web Dashboard:** Build the centralized monitoring UI displaying live exam countdown timers, edge node connectivity, key release status, and WebSocket audit event feeds.
- **End-to-End System Integration:** Coordinate daily end-to-end pipeline execution runs across all modules to identify and resolve integration bottlenecks early.
- **SIH Submission Deliverables:** Author the comprehensive SIH technical report, presentation pitch deck, and architecture diagrams.
- **Demonstration Rehearsal & Backup:** Direct end-to-end dry runs and produce a high-fidelity backup video demonstration.
- **Handoff:** Central dashboard interface, finalized report, presentation slides, and backup demonstration recording.

---

## 🌟 The Two Headline Differentiators

### 1. Hash-Chained, Tamper-Evident Audit Log (Led by Chhavi)
Every single system event is cryptographically sealed into a sequential hash chain:
$$\text{Current Hash} = \text{SHA-256}(\text{Previous Hash} + \text{Timestamp} + \text{Actor} + \text{Action} + \text{Payload Digest})$$
A standalone verification CLI recomputes the chain from genesis and instantly flags any manual alteration or deleted row.

### 2. Forensic Per-Copy Watermarking & Leak Traceability (Led by Vaibhav)
Every printed physical exam paper is dynamically injected with unique, verifiable metadata (Centre ID, Room No., Candidate ID, Timestamp) via embedded QR codes and micro-serials, making any post-print paper photo forensically traceable to its exact origin.

---

## 🏛️ Target Architecture vs. Prototype Scope

| Architecture Tier | Production Vision | Hackathon Prototype Scope |
| :--- | :--- | :--- |
| **Central AI Engine** | AI-assisted Bloom's selection + Human Approval | Question bank + embedding deduplication + human approval endpoint |
| **Cloud Infrastructure** | Multi-region Private Cloud | **Terraform**-provisioned cloud infrastructure (`terraform apply` / `destroy`) |
| **Orchestration** | Full Kubernetes Cluster | **k3s / Docker Compose** (lightweight real K8s manifests & self-healing) |
| **Centre Hardware Auth** | Hardware Security Module (HSM) / Biometrics | **Mutual TLS (mTLS) with self-signed CA** + Scoped JWT RBAC |
| **Physical Separation** | Central Data Centre $\leftrightarrow$ Edge Centres | **Two physical devices** on local network (Authority Host $\leftrightarrow$ Edge Client) |
| **Secure Delivery** | Encrypted Print Stream | In-memory decryption $\rightarrow$ **ReportLab/FPDF dynamic watermarked PDF** |

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

## 🎬 90-Second Demo Script

1. **Encrypted Package:** Show the encrypted package on the edge centre device — prove it is completely unreadable.
2. **Time-Lock Window:** Advance time to the scheduled exam release minute.
3. **Authentication & Key Release:** Edge centre authenticates via mTLS + JWT. Authority verifies credentials and releases the decryption key.
4. **In-Memory Decryption:** Edge client decrypts the paper in memory without writing plaintext to disk.
5. **Traceable Printing:** PDF generated with dynamic per-copy forensic watermarking. Show two distinct generated copies.
6. **Immutable Audit & Tamper Test:** Switch to the live dashboard showing all events logged in real time. Run the verification CLI, then simulate a database tampering attack to prove immediate detection.

---

## 📌 Technical Accuracy Notes

- **AES-256-GCM** is the encryption mechanism; the *time condition* is enforced via server-controlled key release policy (never describe AES itself as "time-lock encryption").
- **SHA-256** provides cryptographic integrity and signing, not encryption.
- **Authentication, encryption, authorization, integrity, and auditing** are five distinct architectural concerns.
