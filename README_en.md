# 🚨 SAP Fraud Detection Pipeline
<div align="right">

![Profile Views](https://komarev.com/ghpvc/?username=Martin-Frei&color=blue&style=for-the-badge)

</div>

**Automated anomaly detection for SAP Sales Orders and Email Verification using Machine Learning and Explainable AI**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![n8n](https://img.shields.io/badge/n8n-EA4B71?style=for-the-badge&logo=n8n&logoColor=white)
![SAP](https://img.shields.io/badge/SAP-0FAAFF?style=for-the-badge&logo=sap&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Claude](https://img.shields.io/badge/Claude_AI-D97757?style=for-the-badge&logo=anthropic&logoColor=white)

---

## 📋 Overview

This project demonstrates two complete Fraud Detection Pipelines:

**Pipeline 1 — SAP Sales Order Anomaly Detection**
Automatically detects suspicious orders in SAP Sales Order data. Combines Isolation Forest with Claude AI — every anomaly is explained with actionable recommendations.

**Pipeline 2 — Email Verification (8-Layer Defense in Depth)**
Verifies email addresses from SAP Business Partner data for validity and spam patterns. Combines DNS, SMTP, mathematics, ML, and AI in a multi-stage architecture with Human-in-the-Loop learning.

---

## 🏗️ Overall Architecture

```
SAP S/4HANA (OData API)
        ↓
n8n Workflow Engine
        ↓
    ┌───┴──────────────────────┐
    ↓                          ↓
Pipeline 1                 Pipeline 2
Sales Order                Email Verification
Anomaly Detection          8-Layer System
    ↓                          ↓
Flask API (Port 5001)      Flask API (Port 5001)
/predict                   /verify
    ↓                          ↓
Isolation Forest           Layer 1: MX Check
+ Claude AI                Layer 2: SMTP Check
    ↓                      Layer 3: Entropy Check
Supabase                   Layer 4: Consonant/Vowel Pattern
sap_order_anomalies        Layer 5: Isolation Forest
                           Layer 6: Claude AI
                           Layer 7: Human in the Loop
                           Layer 8: Auto-Retrain
                               ↓
                           Supabase
                           email_checks
```

---

## 🔍 Pipeline 1 — Sales Order Anomaly Detection

### Three-Layer Detection

| Layer | Technology | Function |
|-------|-----------|----------|
| **Layer 1** | Isolation Forest | Statistical outliers in order data |
| **Layer 2** | Claude AI | Explain anomaly + actionable recommendation |
| **Layer 3** | Frequency Analysis | Patterns over time (peaks, trends) |

### Features for Isolation Forest
| Feature | Description |
|---------|-------------|
| `net_amount` | Order amount — extreme values |
| `customer_encoded` | Customer behavior — unknown customers |
| `user_encoded` | Creator — unusual users |

### Results
```
✅ 900 orders processed
✅ 12 anomalies detected (1.3% rate)
✅ Each anomaly with Claude AI statement
✅ Automated HTML email digest
```

---

## 📧 Pipeline 2 — Email Verification (8-Layer)

### Defense in Depth Architecture

| Layer | Name | Technology | Training? | Decision |
|-------|------|-----------|-----------|----------|
| **L1** | MX Check | DNS | No | Domain has mailserver? |
| **L2** | SMTP Handshake | SMTP | No | Mailbox exists? |
| **L3** | Entropy Check | Shannon Formula | No | Structure random? |
| **L4** | Consonants/Vowels | Speech Pattern | No | Real name? |
| **L5** | Isolation Forest | scikit-learn ML | Yes | Anomaly Detection |
| **L6** | Claude AI | Anthropic API | No | Context + Explanation |
| **L7** | Human in the Loop | Email + Tokens | No | Admin decides |
| **L8** | Auto-Retrain | scikit-learn | Yes | System learns |

### Decision Tree

```
Layer 1: Domain not found (DOMAIN_NOT_FOUND)
→ 🔴 SPAM — block directly, no Claude needed!

Layer 1: Domain ok + Layer 2+: suspicious
→ 🟡 Check Claude! (GoDaddy parking, professional spam)

Layer 3/4/5: Alert (SLIGHT or SUSPICIOUS)
→ 🟡 Check Claude!

All layers ok:
→ 🟢 NORMAL — allow email

Claude says SPAM:
→ 🔴 Layer 7 HIL — Admin gets digest with whitelist link
→ Admin clicks → Layer 8 Retraining starts
→ System learns for next time!
```

---

## 🔬 Layers in Detail

### Layer 1 — MX Check (DNS)
Does the domain have a mailserver? Cheapest & fastest check (~50ms, free).

**Results:**
```
✅ MX_FOUND        → continue to Layer 2
❌ DOMAIN_NOT_FOUND → 🔴 SPAM, done
❌ NO_MX_RECORD    → 🔴 SPAM, done
❌ TIMEOUT/ERROR   → 🔴 SPAM, done
```

**Detection rate Test 1:** 19/20 spam caught by L1 (95%).
*Test 1 had only spam with fake TLDs (.biz, .xyz) — L1 perfect!*

---

### Layer 2 — SMTP Handshake
Does the mailbox exist? SMTP connection without sending email (~500ms-2s, free).

**⚠️ Important — Provider Behavior:**

Large providers **BLOCK** SMTP checks (normal!):
```
🔴 Blocking (doesn't accept SMTP handshake):
   Gmail, Googlemail, Mailbox.org
   Hotmail, iCloud, Protonmail
   GMX, Web.de, T-Online, Freenet
   Posteo, Yahoo, Outlook
```

These provider blocks are **not a spam signal**! Therefore: L2 alert only combined with L4 suspicion.

**Insights:** 
- Layer 2 alone: 164 false positives (90% of all normal emails block!)
- Layer 2 + suspicious local part: 🎯 Good signal

---

### Layer 3 — Entropy Check (Shannon Formula)
Is the name randomly generated? Mathematical chaos measurement (~1ms, free).

```python
Thresholds:
< 1.0             → 🔴 SUSPICIOUS (too simple: aaaaaa)
1.0 - 3.5         → 🟢 OK (normal: martin.mueller)
3.5 - 3.8         → 🟡 SLIGHT (slightly elevated)
> 3.8             → 🔴 SUSPICIOUS (too chaotic: xk7f2q9p)
```

**Examples:**
```
martin      → 2.25 ✅
freimuth    → 2.75 ✅
hkpjpshl    → 3.00 ⚠️ (randomly generated)
kdpmgisnyk  → 3.25 ⚠️
xk7f2q9p    → 3.85 🔴
```

**Insights:** Detects professional spam through real domains that L1+L2 pass. But: Eastern European names also have higher entropy → not decisive alone.

---

### Layer 4 — Consonants + Vowel Check (NEW!)
Does the local part look like a real name? Culturally universal speech pattern.

**The idea:** Every human language has vowels. Bot-generated names have long consonant sequences.

```python
Normalize digraphs (German/English):
sch → s, ch → c, th → t, ph → f

Max consecutive consonants:
≥ 5 or vowel-ratio < 0.15  → 🔴 SUSPICIOUS
≥ 4 or vowel-ratio < 0.25  → 🟡 SLIGHT
else                        → 🟢 OK
```

**Examples:**
```
martin         → max 2 consonants (rt) → 🟢 OK
schmidt        → sch → s (digraph!) → max 2 → 🟢 OK
hochhauser    → chh → ch (digraph!) → max 2 → 🟢 OK

bkk4cij       → bkk (3 consonants) → 🟡 SLIGHT
xjGJXke       → xjGJX (5 consonants!) → 🔴 SUSPICIOUS
pdzp          → pdzp (4 consonants) → 🟡 SLIGHT
```

**Why threshold at 4/5 (not 3/4)?**
German/English names like "Schmidt", "Schweizer" would otherwise have false positives. With digraph normalization it works perfectly.

**Insights (Test 2):** Layer 4 is the **most effective layer**! Detects 8/10 real spam without SMTP check.

---

### Layer 5 — Isolation Forest (ML)
Machine Learning model with 12 features. Finds combinations that are individually inconspicuous.

**Features:**
```
local_entropy, domain_entropy, digit_ratio, special_chars,
local_length, domain_length, is_trusted_domain, 
is_suspicious_tld, has_dot, has_underscore,
shortest_part, longest_part
```

**Trained on:** 1000 synthetic emails (18 cultural backgrounds, 5 spam patterns).

**Training Parameters:**
```python
contamination=0.10  # 10% spam expected
n_estimators=200
random_state=42
```

---

### Layer 6 — Claude AI
Only if at least 1 layer triggers alert. Claude receives **all** results + provides reasoning.

**Input:**
```
Email: xjGJXke1Mo@gmail.com

Layer 1 (MX):       MX_FOUND ✅
Layer 2 (SMTP):     SERVER_DISCONNECTED (Gmail normal!)
Layer 3 (Entropy):  SLIGHT ⚠️
Layer 4 (Consonant): SUSPICIOUS 🔴 (5 consonants!)
Layer 5 (IF):       OK

Assess: SPAM / REAL?
```

**Output Claude:**
```
SPAM — The local part "xjGJXke1Mo" has 5 consecutive 
consonants (xjGJX) without a vowel in between. No real name 
follows this pattern. Despite valid Gmail domain: automated 
spam. Recommendation: block.
```

**Cost Optimization:** ~0.001 USD per call. Since 99% of all emails pass all layers, you save 99% of costs!

---

### Layer 7 — Human in the Loop (HIL)
Admin receives digest email with whitelist link. One click = system learns!

```
"Incorrectly flagged? Click here to whitelist:"
https://localhost:5001/whitelist?token=xyz123&email=name@firm.de

→ Email added to whitelist
→ Token is one-time + time-limited (24h)
→ Isolation Forest retraining starts
→ Next time: similar emails allowed
```

**Routes (planned):**
```
GET  /whitelist?token=xxx&email=yyy
POST /whitelist/check
POST /retrain-email
GET  /blacklist?token=xxx&email=yyy
```

---

### Layer 8 — Auto-Retrain
Isolation Forest retrained regularly with whitelist data. System automatically improves!

**Strategy:**
```
Whitelist grows → every 10 new entries: Retraining
Or: Weekly full retraining
→ Model always knows real domain names
→ Polish names, Asian names, years... all ok
```

---

## 📊 Test Results (200-Email Runs)

### Test 1: Only Spam with Fake TLDs
```
Total:            200 Emails (180 normal + 20 spam)
Total correct:    191/200 (95%) ✅
Spam detected:    20/20 (100%)
False Positives:  9/180 (5%)
Throughslippers:  1 (fgca.info — GoDaddy parking)
needs_claude:     42/200 (21%) — ok
```

**Layer Effectiveness:**
| Layer | Alerts | Of which Spam | Rating |
|-------|--------|---------------|--------|
| L1 | 19 | 19 | ✅ Perfect |
| L2 | 165 (but only 1 spam!) | 1 | ⚠️ Too many |
| L3 | 28 | 6 | 🎯 Good |
| L4/L5 | 25 | 16 | 🎯 Good |

---

### Test 2: 50% Spam with Real Domains
```
Total:            200 Emails (180 normal + 20 spam)
Total correct:    187/200 (93%) ✅
Spam detected:    18/20 (90%)
False Positives:  11/180 (6%)
Throughslippers:  2 (pv60vaiy4va13u1@hotmail.com, P1uRr6YICt@yahoo.de)
needs_claude:     178/200 (89%) ⚠️ too aggressive
```

**Problem found:** Layer 2 rule over-triggers! With real domain, 90% of all emails are marked "needs_claude" (because providers block SMTP).

**Planned Fix:**
```python
# L2 only relevant if local part is suspicious
local_suspicious = (
    digit_ratio > 0.4 or
    local_length > 15 or  
    vowel_ratio < 0.15
)

needs_claude = (
    mx_status == 'MX_FOUND' and (
        (smtp_status not in ('VALID','SKIPPED') and local_suspicious) or
        entropy_status in ('SLIGHT', 'SUSPICIOUS') or
        consonant_status in ('SLIGHT', 'SUSPICIOUS') or
        iso_status == 'SUSPICIOUS'
    )
)
```

---

### Throughslippers Analysis

**Test 1: `1n6kvpuc8d1wj@fgca.info`**
```
Problem: GoDaddy parked domain
→ L1: MX_FOUND ✅ (GoDaddy server!)
→ L2: SMTP_CODE_550
→ L3: SLIGHT ⚠️
→ L4: SLIGHT ⚠️
→ Old needs_claude code: false → throughslip!

With new fix: needs_claude = true → Claude would stop it!
```

**Test 2: `pv60vaiy4va13u1@hotmail.com`**
```
Problem: Very long + many digits
→ L1: MX_FOUND ✅
→ L2: SERVER_DISCONNECTED (Hotmail normal!)
→ L3: OK
→ L4: OK (only 2 consonants at start)
→ L5: OK
→ All layers fail!

Would have helped: digit_ratio check! (4 of 14 = 0.29)
With fix would L2 + local_suspicious = true → Claude ✅
```

**Test 2: `P1uRr6YICt@yahoo.de`**
```
Problem: Upper/lowercase mix + short
→ L1: MX_FOUND ✅
→ L2: SERVER_DISCONNECTED (Yahoo normal!)
→ L3: OK
→ L4: SLIGHT 🟡 (rr = 2 consonants but OK)
→ L5: OK
→ Only L4 SLIGHT — not enough!

With fix: SLIGHT in L4 + L2 suspicion = needs_claude true ✅
```

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Data Source | SAP S/4HANA Cloud (OData V2) | Orders + Business Partner |
| Orchestration | n8n (Self-Hosted) | Workflow Automation |
| ML Models | Isolation Forest (scikit-learn) | Anomaly detection (Order + Email) |
| AI Explanation | Claude Haiku (Anthropic API) | Explainable AI |
| Prediction API | Flask (Python) | ML Model Serving |
| Database | Supabase (PostgreSQL) | Orders + Anomalies + Email Checks |
| Notification | GMX SMTP | HTML Email Digest |

---

## 📂 Project Structure

```
sap_n8n_demo/
├── A_dokumentation/
│   ├── 2026-05-15_sap_n8n_claude_fraud.md
│   ├── 2026-05-20_sap_n8n_order_detection.md
│   ├── 2026-05-21_sap_n8n_order_detection.md
│   ├── 2026-05-29_email_Verification_Planung.md
│   ├── 2026-05-31_aufbu_optimierung_erkenntnisse_layer_3_4.md
│   ├── 2026-05-31_Layer_5_and_supabase.md
│   ├── 2026-05-31_result_saved_supabase.md
│   ├── 2026-05-31_supabase_table_erstellen.md
│   ├── 2026-06-01_verify_all_erkenntnisse_8_layer.md
│   └── 2026-06-01_rsult_csv_run.md
├── data/
│   ├── test_emails.json                ← 50 Test Emails
│   ├── verify_results_20260601_0641.csv ← Test 1 Results (200 Emails)
│   └── verify_results_20260601_1238.csv ← Test 2 Results (200 Emails)
├── models/
│   ├── sap_isolation_forest.pkl
│   ├── label_encoder_customer.pkl
│   ├── label_encoder_user.pkl
│   ├── email_isolation_forest.pkl
│   └── email_feature_cols.pkl
├── python/
│   ├── generate/
│   │   ├── generator.py                ← Email Generator (18 Cultural Backgrounds)
│   │   ├── config.yaml                 ← Configuration
│   │   └── examples/
│   │       ├── sample_1000.csv         ← Training Data
│   │       └── sample_200_real_domain.csv ← Test 2 Data
│   ├── predict/
│   │   └── predict_server.py           ← Flask Server (all layers)
│   ├── training/
│   │   ├── isolation_forest_train.py   ← SAP Model Training
│   │   ├── email_forest_train.py       ← Email Model Training
│   │   └── verify_all.py               ← Batch Verification Test
│   ├── utils/
│   │   └── sales_order_eda.py
│   └── requirements.txt
├── workflows/
│   ├── sap_claude_analyse_v1.json
│   ├── sap_order_validating.json
│   └── email_verification_v1.json
├── .env                                 ← API Keys (not in Git)
├── .gitignore
├── README.md
└── start_n8n.bat
```

---

## 🚀 Setup & Installation

### Prerequisites
- Node.js v22 (for n8n)
- Python 3.x
- SAP API Business Hub Account
- Anthropic API Key
- Supabase Project

### 1. Clone Repository
```bash
git clone https://github.com/Martin-Frei/sap_n8n_demo.git
cd sap_n8n_demo
```

### 2. Python Environment
```bash
python -m venv venv_sap
venv_sap\Scripts\activate
pip install -r python/requirements.txt
```

### 3. Environment Variables
```bash
# Create .env file
SAP_API_KEY=your_sap_key
ANTHROPIC_API_KEY=your_anthropic_key
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_supabase_key
```

### 4. Train Models
```bash
# SAP Order Model
python python/training/isolation_forest_train.py

# Email Generator
cd python/generate
python generator.py
cd ../..

# Email Model
python python/training/email_forest_train.py
```

### 5. Start Flask Server
```bash
python python/predict/predict_server.py
# → runs on http://localhost:5001
# ✅ SAP Model loaded
# ✅ Email Model loaded
```

### 6. Start n8n
```bash
start_n8n.bat
# → runs on http://localhost:5678
```

### 7. Import Workflows
```
n8n → Import from File → workflows/sap_order_validating.json
n8n → Import from File → workflows/email_verification_v1.json
```

---

## 📸 Screenshots & Evidence

### n8n SAP Order Workflow
![SAP Workflow](screenshots/n8n_workflow.jpg)

### n8n Email Verification Workflow
![Email Workflow](screenshots/n8n_email_workflow.png)

### Email Digest Output
![Email Digest](screenshots/email_digest.jpg)

### Layer 3+4 Test Output
![Test Layer 3+4](screenshots/test_layer34_output.png)

### SAP Anomalies in Supabase
![Supabase Anomalies](screenshots/supabase_anomalien.jpg)

### Email Checks in Supabase
![Supabase Email Checks](screenshots/supabase_email_checks.png)

---

## 🧪 Testing

### Test Flask Server Health
```bash
curl http://localhost:5001/health
```

### Test Email Verification (5 Emails)
```bash
curl -X POST http://localhost:5001/verify \
  -H "Content-Type: application/json" \
  -d '[
    {"EmailAddress": "martin@example.com", "Person": "Martin"},
    {"EmailAddress": "spam@spam.biz", "Person": "Spam Bot"}
  ]'
```

### Test SAP Order Prediction
```bash
curl -X POST http://localhost:5001/predict \
  -H "Content-Type: application/json" \
  -d '[
    {"sales_order": "4500015", "customer_id": "17100001", "net_amount": 52.65, "created_by": "WEBSERVICE"}
  ]'
```

---

## ⚠️ Known Limitations

**SAP Sandbox:**
The sandbox contains static test data. In production, the workflow would process new orders and business partners daily.

**Email Model:**
Trained on synthetic data (1000 emails, 18 cultural backgrounds). With real production data (whitelist feedback, HIL) accuracy increases rapidly.

**needs_claude Over-Triggering:**
Test 2 showed: Layer 2 + provider blocks = 178/200 (89%) emails to Claude. Fix is designed (local_suspicious check), not yet deployed.

**Throughslippers:**
2 emails in Test 2 slipped through all layers. Both would be caught with the planned `local_suspicious` fix for Layer 2.

---

## 📚 Documentation

Detailed step-by-step documentation in `A_dokumentation/`:

| Date | Topic |
|------|-------|
| 2026-05-15 | SAP API Setup, n8n, first Claude workflow |
| 2026-05-20 | Sales Order Pipeline, EDA, Isolation Forest |
| 2026-05-21 | Flask Server, End-to-End, Email Digest |
| 2026-05-29 | Email Verification Planning, 5-Layer Concept |
| 2026-05-31 | Layer 3+4 Setup, Generator, n8n Workflow |
| 2026-06-01 | 8-Layer Architecture, 200-email tests, Insights |

---

## 🌍 Email Generator — Open Source

The synthetic email address generator is available as its own tool:

```
python/generate/
├── generator.py   ← configurable via config.yaml
└── config.yaml    ← 18 cultural backgrounds, spam patterns, domains
```

**Features:**
- 180 first names + 180 last names from 18 cultural backgrounds
- RFC 2606 compliant domains (never reachable, never real!)
- 5 different spam patterns
- No cultural bias — evaluate structure not names

---

## 👤 Author

**Martin Freimuth**
- 🌐 [Portfolio](https://www.martin-freimuth.dev)
- 💼 [LinkedIn](https://www.linkedin.com/in/martin-freimuth/)
- 📧 martin@houseofstocks.dev

---

## 📝 License

This project is for demonstration and learning purposes.
