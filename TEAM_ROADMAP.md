# 10-Day Team Execution Roadmap & Daily Breakdown

This document defines the daily tasks, ownership, dependencies, and handoffs for all 6 team roles in **Bharat AI**.

---

## 📋 Team Ownership Matrix

| Person | Member | Role / Vertical Slice | Main Tech Stack |
| :--- | :--- | :--- | :--- |
| **Person 1** | **Nupur** | Question Bank + AI Selection Engine | Python, SQLite/MongoDB, Sentence-Transformers |
| **Person 2** | **Parth** | Crypto Core + Zero-Trust Auth | Cryptography (AES-256-GCM, SHA-256), OpenSSL mTLS, PyJWT |
| **Person 3** | **Janaki** | Backend Services + IaC | FastAPI, Docker Compose, k3s, Terraform |
| **Person 4** | **Vaibhav** | Edge Centre Client + Physical Demo | Python, ReportLab/FPDF, QR Code, Socket/HTTP |
| **Person 5** | **Chhavi** | Audit Trail + Hash-Chain Engine | Python, Hashlib, SQLite, WebSockets |
| **Person 6** | **Vaibhav** | Dashboard + Integration + Documentation | Streamlit / React, WebSockets, Prometheus, SIH Report/PPT |

---

## 👤 Person 1: Nupur — Question Bank & AI Selection Engine
**Vertical:** Tier 1 Central AI Engine (Front Half)  
**Tools:** Python, SQLite / MongoDB, `sentence-transformers` / LLM API

- [ ] **Days 1–2: Schema & Paper Assembler**
  - Design question schema: `id`, `topic`, `subtopic`, `difficulty`, `marks`, `bloom_level`, `tags`, `last_used_year`, `embedding_vector`.
  - Seed dataset with 40–60 realistic questions across 2–3 subjects.
  - Implement `assemble_paper(subject, difficulty_distribution, total_marks) -> paper_json`.
- [ ] **Days 3–5: AI Deduplication & Human Authorization**
  - Implement vector similarity check against past exam question embeddings (flags questions > 0.85 cosine similarity).
  - Build the Human-in-the-Loop approval endpoint (`POST /paper/approve` / `POST /paper/reject`) — ensuring AI assists, but human authorities sign off.
- [ ] **Days 6–7: Difficulty Balancing & Analytics**
  - Implement Bloom's taxonomy weighted balancing.
  - Add question bank analytics (usage frequency, topic coverage gap detection).
- [ ] **Day 8: Integration with Backend**
  - Integrate with Person 3's API endpoints; verify output schema conforms to Person 2's encryption input.
- [ ] **Days 9–10: Documentation & Testing**
  - Write the AI Selection & Bloom's Taxonomy section in the SIH report/slides.
  - Assist with end-to-end dry runs.
- **Handoff to Person 2 & 3:** Standardized, validated plain paper JSON dictionary.

---

## 👤 Person 2: Parth — Crypto Core & Zero-Trust Auth
**Vertical:** Security Architecture & Cryptographic Engine  
**Tools:** Python `cryptography`, OpenSSL, `PyJWT`

- [ ] **Days 1–2: AES-GCM + SHA-256 Crypto Module**
  - Implement `sign_and_encrypt(paper_dict, secret_key) -> encrypted_package`.
  - Implement `decrypt_and_verify(encrypted_package, secret_key) -> paper_dict`.
  - Comprehensive unit tests: tampered ciphertext fails, tampered signature fails, wrong key fails.
- [ ] **Days 3–5: Self-Signed CA & Mutual TLS (mTLS)**
  - Script OpenSSL Root CA creation and issue X.509 certs for Central Authority and Edge Centre clients.
  - Configure mTLS communication between Authority and Edge client services.
- [ ] **Days 6–7: Scoped JWT Role-Based Access Control**
  - Implement granular JWT authorization with claims (`centre-role`, `authority-role`, `invigilator-role`, `allowed_exam_id`, `expiry`).
- [ ] **Day 8: Adversarial & Pentesting Validation**
  - Execute attack scenarios: replay old key requests, decrypt prior to release timestamp, forge JWT tokens, inject tampered payload.
  - Document attack test cases and failure logs for the SIH technical report.
- [ ] **Days 9–10: Security Architecture Report**
  - Author the formal Security Architecture chapter (explicitly distinguishing encryption vs. integrity vs. authorization vs. time-lock).
- **Handoff to Person 3 & 4:** Modular crypto library + CA certificates + JWT validator.

---

## 👤 Person 3: Janaki — Backend Services & Infrastructure as Code
**Vertical:** Tiers 2 & 3 Microservices & IaC  
**Tools:** FastAPI, Uvicorn, Docker Compose, k3s, Terraform

- [ ] **Days 1–2: API Scaffolding & Stubs**
  - Scaffold FastAPI modular services: `auth_service`, `paper_service`, `timelock_service`, `key_release_service`.
  - Provide documented mock endpoints so frontend and client team members can develop without blocking.
- [ ] **Days 3–4: Core Logic Integration & Docker Compose**
  - Wire Nupur's (Person 1) question assembler and Parth's (Person 2) crypto engine into the API flow.
  - Create multi-container `docker-compose.yml` for unified local execution.
- [ ] **Days 5–6: Kubernetes (k3s) Manifests & Self-Healing**
  - Write Kubernetes Deployment, Service, and ConfigMap manifests for k3s.
  - Demonstrate self-healing (killing a pod during demo and showing immediate K8s auto-recovery).
- [ ] **Days 6–7: Terraform Infrastructure as Code (IaC)**
  - Write `main.tf`, `variables.tf`, `outputs.tf` for provisioning host nodes / k3s cluster.
  - Demonstrate one-click `terraform apply` and clean `terraform destroy`.
- [ ] **Day 8: Production Hardening**
  - Add rate limiting, connection retries, structured error handling, and health-check endpoints.
- [ ] **Days 9–10: Integration & Load Testing**
  - Coordinate full-system stress tests with Vaibhav (Person 6).
- **Handoff to Person 4 & 6:** Stable, containerized, documented REST/WebSocket APIs.

---

## 👤 Person 4: Vaibhav — Edge Centre Client & Physical Demo
**Vertical:** Tier 4 Edge Centre Deployment & Secure Printing  
**Tools:** Python, ReportLab / FPDF, QRCode, Physical Laptop / Raspberry Pi

- [ ] **Days 1–3: Edge Client Sequence Skeleton**
  - Implement edge workflow: `Authenticate (mTLS + JWT)` $\rightarrow$ `Fetch Encrypted Package` $\rightarrow$ `Poll Time-Lock` $\rightarrow$ `Request Key at Release Time` $\rightarrow$ `In-Memory Decryption`.
- [ ] **Days 4–6: Real Network Deployment (Dual-Device Setup)**
  - Deploy edge client onto a separate physical laptop / Raspberry Pi on the local network (no localhost cheats).
  - Wire real encrypted payloads from backend services.
- [ ] **Days 7–8: Forensic Per-Copy Watermarking**
  - Build dynamic PDF generator with per-copy forensic watermarking:
    - Unique QR code encoding: `Centre ID + Room Number + Candidate ID + Micro-Timestamp`.
    - Subtle background steganographic micro-pattern or tracking serial.
  - Demonstrate printing 2 copies with distinct verifiable watermarks.
- [ ] **Days 9–10: Live Physical Demo Rehearsal**
  - Rehearse edge-to-cloud execution flow repeatedly under simulated network drops.
- **Handoff:** End-to-end demonstrable edge application and printed paper samples.

---

## 👤 Person 5: Chhavi — Tamper-Evident Hash-Chained Audit Trail
**Vertical:** Headline Differentiator 1 — Immutable Audit Trail  
**Tools:** Python, Hashlib, SQLite / MongoDB, WebSockets

- [ ] **Days 1–3: Cryptographic Hash-Chain Engine**
  - Design audit event schema: `event_id`, `actor`, `action`, `centre_id`, `timestamp`, `details_digest`, `prev_hash`, `current_hash`.
  - Implement `append_event(actor, action, details) -> event` and `verify_chain(events) -> (is_valid, broken_index)`.
- [ ] **Days 4–5: Middleware Audit Interceptors**
  - Integrate audit interceptors across all backend endpoints (logging auth attempts, key queries, paper assembly, print triggers, unauthorized accesses).
  - Stream events via WebSockets to the live monitoring dashboard.
- [ ] **Days 6–7: Standalone Verification CLI Tool**
  - Build `audit_verify_cli.py` — an independent executable judges can run to mathematically verify the entire log ledger.
- [ ] **Day 8: Live Tamper-Proof Attack Demo**
  - Script a live tampering demo: alter a database record directly, run the verification CLI, and highlight exact line and hash mismatch.
- [ ] **Days 9–10: SIH Documentation & Headline Pitch**
  - Write the Audit Ledger & Cryptographic Integrity chapter in the final submission.
- **Handoff:** Independent audit verification tool and live event streaming API.

---

## 👤 Person 6: Vaibhav — Live Dashboard, Integration & Documentation
**Vertical:** Headline Differentiator 2, UI Dashboard, System Integration & SIH Deliverables  
**Tools:** Streamlit / React + Tailwind, WebSockets, Prometheus, PowerPoint / Canva

- [ ] **Days 1–3: Unified Live Dashboard Shell**
  - Build interactive UI: Exam Countdown Timer, Node Health Grid, Live Audit Log Feed, Centre Authorization Status.
- [ ] **Days 4–6: Real-Time Event Integration**
  - Connect dashboard to Chhavi's (Person 5) WebSocket audit feed and Janaki's (Person 3) microservice health metrics.
- [ ] **Days 7–8: Daily Full-Pipeline Integration Runs**
  - Conduct daily integration runs end-to-end (`Generate` $\rightarrow$ `Encrypt` $\rightarrow$ `Time-Lock` $\rightarrow$ `Authorize` $\rightarrow$ `Decrypt` $\rightarrow$ `Print` $\rightarrow$ `Audit`).
  - Draft SIH 2026 Presentation PPT and Technical Report.
- [ ] **Day 9: Final Polish & Dry Runs**
  - Finalize submission materials, coordinate 2 complete team rehearsal dry-runs.
- [ ] **Day 10: Buffer & Backup Video Capture**
  - Record full screen + physical camera backup video of a complete successful run to guarantee safety against venue network failures.

---

## ⏱️ Cross-Cutting Rhythm & Milestones

- **End of Day 3:** First end-to-end prototype run (stubs + core logic).
- **End of Day 6:** Both key differentiators functional (tamper-evident hash-chain verification & forensic per-copy watermarking).
- **End of Day 8:** Adversarial tests complete; Terraform & k3s deployment verified.
- **Day 9:** All documentation and slides locked; 2 formal dry-runs completed.
- **Day 10:** Buffer day — video backup recorded, strictly zero new code.
