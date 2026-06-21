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
Automatically detects suspicious orders in SAP Sales Order data. Combines Isolation Forest with Claude AI — every anomaly is explained and accompanied by a recommended action.

**Pipeline 2 — Email Verification (5-Layer)**
Validates email addresses from SAP Business Partner data for validity and spam patterns. Combines DNS, SMTP, mathematics, ML, and AI into a Defense-in-Depth architecture.

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
Anomaly Detection          5-Layer System
    ↓                          ↓
Flask API (Port 5001)      Flask API (Port 5001)
/predict                   /verify
    ↓                          ↓
Isolation Forest           Layer 1: MX Check
+ Claude AI                Layer 2: SMTP Check
    ↓                      Layer 3: Entropy Check
Supabase                   Layer 4: Isolation Forest
sap_order_anomalies        Layer 5: Claude AI
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
| **Layer 2** | Claude AI | Explain anomaly + recommended action |
| **Layer 3** | Frequency Analysis | Patterns over time (peaks, trends) |

### Features for Isolation Forest
| Feature | Description |
|---------|-------------|
| `net_amount` | Order amount — extreme values |
| `customer_encoded` | Customer behaviour — unknown customers |
| `user_encoded` | Creator — unusual users |

### Results
```
✅ 900 orders processed
✅ 12 anomalies detected (1.3% rate)
✅ Every anomaly with Claude AI statement
✅ Automated HTML email digest
```

---

## 📧 Pipeline 2 — Email Verification (5-Layer)

### Defense in Depth Architecture

| Layer | Technology | Function | Training required? |
|-------|-----------|----------|--------------------|
| **Layer 1** | DNS MX Check | Does domain have a mail server? | No |
| **Layer 2** | SMTP Handshake | Does mailbox exist? | No |
| **Layer 3** | Entropy Check | Is structure suspicious? (mathematics) | No |
| **Layer 4** | Isolation Forest | ML anomaly detection | Yes |
| **Layer 5** | Claude AI | Context + explanation | No |
| **Layer 6** | Human in the Loop | Admin decision (planned) | No |

### Layer 5 Rule
```
🟡 SLIGHT or 🔴 SUSPICIOUS at Layer 3 or 4 → Claude reviews
🟢 OK at both → only Layer 1+2 as safeguard
```

### Entropy Check (Layer 3)
```
< 1.0          → 🔴 SUSPICIOUS  (too simple: aaaaaaa@...)
1.0 - 3.5      → 🟢 OK          (normal: martin.mueller@...)
3.5 - 3.8      → 🟡 SLIGHT      (slightly elevated)
> 3.8          → 🔴 SUSPICIOUS  (too chaotic: xk7f2q9p@...)
```

### Email Isolation Forest Features
```python
feature_cols = [
    'local_entropy', 'domain_entropy', 'digit_ratio',
    'special_chars', 'local_length', 'domain_length',
    'is_trusted_domain', 'is_suspicious_tld',
    'has_dot', 'has_underscore',
    'shortest_part', 'longest_part'
]
```

### Test Results (50 Emails)
```
Total correct:    44/50 (88%)
Spam detected:    4/5
False positives:  5/45 → forwarded to Claude (Layer 5)
```

### GDPR Concept
```
Email is NEVER stored!
→ simpleHash for recognition (whitelist)
→ Features anonymised in Supabase
→ Deletion after 90 days (expires_at)
```

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Data source | SAP S/4HANA Cloud (OData V2) | Orders + Business Partner |
| Orchestration | n8n (Self-Hosted) | Workflow Automation |
| ML Model 1 | Isolation Forest (scikit-learn) | SAP Order Anomaly Detection |
| ML Model 2 | Isolation Forest (scikit-learn) | Email Anomaly Detection |
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
│   ├── 2026-05-31_aufbau_optimierung_erkenntniss_layer_3_4.md
│   └── 2026-05-31_email_verification_workflow_komplett.md
├── data/
│   └── test_emails.json          ← 50 test emails
├── models/
│   ├── sap_isolation_forest.pkl
│   ├── label_encoder_customer.pkl
│   ├── label_encoder_user.pkl
│   ├── email_isolation_forest.pkl ← NEW
│   └── email_feature_cols.pkl     ← NEW
├── python/
│   ├── generate/
│   │   ├── generator.py          ← Email Generator (18 cultural backgrounds)
│   │   ├── config.yaml           ← Configuration
│   │   └── examples/
│   │       └── sample_1000.csv   ← Training data
│   ├── predict/
│   │   └── predict_server.py     ← Flask Server (Layer 1-4 + Layer 6)
│   ├── training/
│   │   ├── isolation_forest_train.py
│   │   ├── email_forest_train.py  ← NEW
│   │   └── test_layer34.py        ← NEW visual test
│   ├── utils/
│   │   └── sales_order_eda.py
│   └── requirements.txt
├── workflows/
│   ├── sap_claude_analyse_v1.json
│   ├── sap_order_validating.json
│   └── email_verification_v1.json ← NEW
├── .env                 ← API Keys (not in Git)
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
# SAP Order model
python python/training/isolation_forest_train.py

# Email Generator
cd python/generate
python generator.py
cd ../..

# Email model
python python/training/email_forest_train.py
```

### 5. Start Flask Server
```bash
python python/predict/predict_server.py
# → running on http://localhost:5001
# ✅ SAP model loaded
# ✅ Email model loaded
```

### 6. Start n8n
```bash
start_n8n.bat
```

### 7. Import Workflows
```
n8n → Import from File → workflows/sap_order_validating.json
n8n → Import from File → workflows/email_verification_v1.json
```

---

## 📸 Screenshots

### Pipeline 1 — SAP Order Workflow
![SAP Workflow](screenshots/n8n_workflow.jpg)

### Email Digest
![Email Digest](screenshots/email_digest.jpg)

### SAP Anomalies in Supabase
![Supabase Anomalies](screenshots/supabase_anomalien.jpg)

### Pipeline 2 — Email Verification Workflow
![Email Workflow](screenshots/n8n_email_workflow.png)

### Layer 3+4 Test Output
![Test Layer 3+4](screenshots/test_layer34_output.png)

### Email Checks in Supabase
![Supabase Email](screenshots/supabase_email_checks.png)

---

## 🌍 Email Generator — Open Source

The synthetic email address generator is available as a standalone tool:

```
python/generate/
├── generator.py   ← configurable via config.yaml
└── config.yaml    ← 18 cultural backgrounds, spam patterns, domains
```

**Features:**
- 180 first names + 180 last names from 18 cultural backgrounds
- RFC 2606 compliant domains (never reachable, never real!)
- 5 different spam patterns
- No cultural bias — structure evaluated, not names

---

## ⚠️ Known Limitations

**SAP Sandbox:**
The sandbox contains static test data. In production, the workflow would process new orders and business partners daily.

**Email Model:**
Trained on synthetic data → 88% detection rate. With real production data (honeypot, HIL feedback) accuracy increases.

---

## 📚 Documentation

Detailed step-by-step documentation in `A_dokumentation/`:

| Date | Topic |
|------|-------|
| 2026-05-15 | SAP API setup, n8n, first Claude workflow |
| 2026-05-20 | Sales Order Pipeline, EDA, Isolation Forest |
| 2026-05-21 | Flask Server, End-to-End, Email Digest |
| 2026-05-29 | Email Verification planning, 5-Layer concept |
| 2026-05-31 | Layer 3+4 build, Generator, n8n workflow |

---

## 👤 Author

**Martin Freimuth**
- 🌐 [Portfolio](https://www.martin-freimuth.dev)
- 💼 [LinkedIn](https://www.linkedin.com/in/martin-freimuth/)
- 📧 martin@houseofstocks.dev

---

## 📝 License

This project is intended for demonstration and learning purposes.
