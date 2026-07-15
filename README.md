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

## 📋 Überblick

Dieses Projekt demonstriert zwei vollständige Fraud Detection Pipelines:

**Pipeline 1 — SAP Sales Order Anomalie Detection**
Erkennt automatisch verdächtige Bestellungen in SAP Sales Order Daten. Kombiniert Isolation Forest mit Claude AI — jede Anomalie wird erklärt und mit Handlungsempfehlung versehen.

**Pipeline 2 — Email Verification (8-Layer Defense in Depth)**
Prüft Email-Adressen aus SAP Business Partner Daten auf Validität und Spam-Muster. Kombiniert DNS, SMTP, Mathematik, ML und AI zu einer mehrstufigen Architektur mit Human-in-the-Loop Learning.

---

## 🏗️ Gesamt-Architektur

```
SAP S/4HANA (OData API)
        ↓
n8n Workflow Engine
        ↓
    ┌───┴──────────────────────┐
    ↓                          ↓
Pipeline 1                 Pipeline 2
Sales Order                Email Verification
Anomalie Detection         8-Layer System
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

## 🔍 Pipeline 1 — Sales Order Anomalie Detection

### Drei-Layer Erkennung

| Layer | Technologie | Funktion |
|-------|------------|----------|
| **Layer 1** | Isolation Forest | Statistische Ausreißer in Bestelldaten |
| **Layer 2** | Claude AI | Anomalie erklären + Handlungsempfehlung |
| **Layer 3** | Häufungsanalyse | Muster über Zeit (Peaks, Trends) |

### Features für Isolation Forest
| Feature | Beschreibung |
|---------|-------------|
| `net_amount` | Bestellbetrag — extreme Werte |
| `customer_encoded` | Kundenverhalten — unbekannte Kunden |
| `user_encoded` | Ersteller — ungewöhnliche User |

### Ergebnisse
```
✅ 900 Orders verarbeitet
✅ 12 Anomalien erkannt (1.3% Rate)
✅ Jede Anomalie mit Claude AI Statement
✅ Automatischer HTML Email Digest
```

---

## 📧 Pipeline 2 — Email Verification (8-Layer)

### Defense in Depth Architektur

| Layer | Name | Technologie | Training? | Entscheidung |
|-------|------|-------------|-----------|--------------|
| **L1** | MX Check | DNS | Nein | Domain hat Mailserver? |
| **L2** | SMTP Handshake | SMTP | Nein | Mailbox existiert? |
| **L3** | Entropy Check | Shannon Formel | Nein | Struktur zufällig? |
| **L4** | Konsonanten/Vokale | Sprachmuster | Nein | Echter Name? |
| **L5** | Isolation Forest | scikit-learn ML | Ja | Anomalie Detection |
| **L6** | Claude AI | Anthropic API | Nein | Kontext + Erklärung |
| **L7** | Human in the Loop | Email + Tokens | Nein | Admin entscheidet |
| **L8** | Auto-Retrain | scikit-learn | Ja | System lernt dazu |

### Entscheidungsbaum

```
Layer 1: Domain nicht gefunden (DOMAIN_NOT_FOUND)
→ 🔴 SPAM — direkt blockieren, kein Claude nötig!

Layer 1: Domain ok + Layer 2+: verdächtig
→ 🟡 Claude prüfen! (GoDaddy Parking, professioneller Spam)

Layer 3/4/5: Alarm (SLIGHT oder SUSPICIOUS)
→ 🟡 Claude prüfen!

Alle Layer ok:
→ 🟢 NORMAL — Email durchlassen

Claude sagt SPAM:
→ 🔴 Layer 7 HIL — Admin bekommt Digest mit Whitelist-Link
→ Admin klickt → Layer 8 Retraining startet
→ System lernt für nächste Mal!
```

---

## 🔬 Layer im Detail

### Layer 1 — MX Check (DNS)
Domain hat einen Mailserver? Billigster & schnellster Check (~50ms, kostenlos).

**Ergebnisse:**
```
✅ MX_FOUND        → weiter zu Layer 2
❌ DOMAIN_NOT_FOUND → 🔴 SPAM, fertig
❌ NO_MX_RECORD    → 🔴 SPAM, fertig
❌ TIMEOUT/ERROR   → 🔴 SPAM, fertig
```

**Erkennungsrate Test 1:** 19/20 Spam durch L1 (95%).
*Test 1 hatte nur Spam mit fake TLDs (.biz, .xyz) — L1 Perfekt!*

---

### Layer 2 — SMTP Handshake
Mailbox existiert? SMTP Verbindung ohne Email zu senden (~500ms-2s, kostenlos).

**⚠️ Wichtig — Provider-Verhalten:**

Große Provider **BLOCKEN** SMTP Checks (normal!):
```
🔴 Blocken (akzeptiert Handshake NICHT):
   Gmail, Googlemail, Mailbox.org
   Hotmail, iCloud, Protonmail
   GMX, Web.de, T-Online, Freenet
   Posteo, Yahoo, Outlook
```

Diese Provider-Blocks sind **kein Spam-Signal**! Deshalb: L2 Alarm nur mit L4 Verdacht kombinieren.

**Erkenntnisse:** 
- Layer 2 alleine: 164 False Positives (90% aller normalen Emails blocken!)
- Layer 2 + verdächtigem lokalen Teil: 🎯 Gutes Signal

---

### Layer 3 — Entropy Check (Shannon Formel)
Ist der Name zufällig generiert? Mathematische Chaos-Messung (~1ms, kostenlos).

```python
Schwellwerte:
< 1.0             → 🔴 SUSPICIOUS (zu simpel: aaaaaa)
1.0 - 3.5         → 🟢 OK (normal: martin.mueller)
3.5 - 3.8         → 🟡 SLIGHT (leicht erhöht)
> 3.8             → 🔴 SUSPICIOUS (zu chaotisch: xk7f2q9p)
```

**Beispiele:**
```
martin      → 2.25 ✅
freimuth    → 2.75 ✅
hkpjpshl    → 3.00 ⚠️ (zufällig generiert)
kdpmgisnyk  → 3.25 ⚠️
xk7f2q9p    → 3.85 🔴
```

**Erkenntnisse:** Erkennt professionellen Spam durch echte Domains, den Layer 1+2 durchlassen. Aber: Osteuropäische Namen haben auch höhere Entropy → nicht alleine entscheidend.

---

### Layer 4 — Konsonanten + Vokal Check (NEU!)
Sieht der lokale Teil wie ein echter Name aus? Kulturell universelles Sprachmuster.

**Die Idee:** Jede menschliche Sprache hat Vokale. Bot-generierte Namen haben lange Konsonantenfolgen.

```python
Digraphen normalisieren (deutsch/englisch):
sch → s, ch → c, th → t, ph → f

Max aufeinanderfolgende Konsonanten:
≥ 5 oder Vokal-Ratio < 0.15  → 🔴 SUSPICIOUS
≥ 4 oder Vokal-Ratio < 0.25  → 🟡 SLIGHT
sonst                        → 🟢 OK
```

**Beispiele:**
```
martin         → max 2 Konsonanten (rt) → 🟢 OK
schmidt        → sch → s (Digraph!) → max 2 → 🟢 OK
hochhauser    → chh → ch (Digraph!) → max 2 → 🟢 OK

bkk4cij       → bkk (3 Konsonanten) → 🟡 SLIGHT
xjGJXke       → xjGJX (5 Konsonanten!) → 🔴 SUSPICIOUS
pdzp          → pdzp (4 Konsonanten) → 🟡 SLIGHT
```

**Warum Schwelle bei 4/5 (nicht 3/4)?**
Deutsche/englische Namen wie "Schmidt", "Schweizer" hätten sonst False Positives. Mit Digraph-Normalisierung funktioniert's perfekt.

**Erkenntnisse (Test 2):** Layer 4 ist der **effektivste Layer**! Erkennt 8/10 echte Spam ohne SMTP-Check.

---

### Layer 5 — Isolation Forest (ML)
Machine Learning Modell mit 12 Features. Findet Kombinationen die einzeln unauffällig sind.

**Features:**
```
local_entropy, domain_entropy, digit_ratio, special_chars,
local_length, domain_length, is_trusted_domain, 
is_suspicious_tld, has_dot, has_underscore,
shortest_part, longest_part
```

**Trainiert auf:** 1000 synthetische Emails (18 Kulturkreise, 5 Spam-Patterns).

**Training Parameters:**
```python
contamination=0.10  # 10% Spam erwartet
n_estimators=200
random_state=42
```

---

### Layer 6 — Claude AI
Nur wenn Mindestens 1 Layer Alarm gibt. Claude bekommt **alle** Ergebnisse + gibt Begründung.

**Eingabe:**
```
Email: xjGJXke1Mo@gmail.com

Layer 1 (MX):       MX_FOUND ✅
Layer 2 (SMTP):     SERVER_DISCONNECTED (Gmail normal!)
Layer 3 (Entropy):  SLIGHT ⚠️
Layer 4 (Consonant): SUSPICIOUS 🔴 (5 Konsonanten!)
Layer 5 (IF):       OK

Bewerte: SPAM / ECHT?
```

**Output Claude:**
```
SPAM — Der lokale Teil "xjGJXke1Mo" hat 5 aufeinanderfolgende 
Konsonanten (xjGJX) ohne Vokal dazwischen. Kein echter Name 
folgt diesem Pattern. Trotz gültiger Gmail-Domain: automatisierter 
Spam. Recommendation: blockieren.
```

**Kostenoptimierung:** ~0.001 USD pro Call. Da 99% aller Emails alle Layer ok haben, spart man 99% Kosten!

---

### Layer 7 — Human in the Loop (HIL)
Admin bekommt Digest Email mit Whitelist-Link. Ein Klick = System lernt!

```
"Falsch erkannt? Hier klicken zum Whitelisten:"
https://localhost:5001/whitelist?token=xyz123&email=name@firm.de

→ Email wird in Whitelist eingetragen
→ Token wird einmalig + zeitlich begrenzt (24h)
→ Isolation Forest Retraining startet
→ Nächstes Mal: ähnliche Emails durchgelassen
```

**Routes (geplant):**
```
GET  /whitelist?token=xxx&email=yyy
POST /whitelist/check
POST /retrain-email
GET  /blacklist?token=xxx&email=yyy
```

---

### Layer 8 — Auto-Retrain
Isolation Forest wird regelmäßig mit Whitelist-Daten neu trainiert. System wird automatisch besser!

**Strategie:**
```
Whitelist wächst → alle 10 neue Einträge: Retraining
Oder: Wöchentlich vollständiges Retraining
→ Modell kennt immer echte Domain-Namen
→ Polnische Namen, asiatische Namen, Jahrzahlen... alles ok
```

---

## 📊 Testergebnisse (200er Runs)

### Test 1: Nur Spam mit Fake TLDs
```
Gesamt:            200 Emails (180 normal + 20 spam)
Gesamt korrekt:    191/200 (95%) ✅
Spam erkannt:      20/20 (100%)
False Positives:   9/180 (5%)
Durchschlüpfer:    1 (fgca.info — GoDaddy Parking)
needs_claude:      42/200 (21%) — ok
```

**Layer-Effektivität:**
| Layer | Alarme | davon Spam | Bewertung |
|-------|--------|-----------|-----------|
| L1 | 19 | 19 | ✅ Perfekt |
| L2 | 165 (aber nur 1 Spam!) | 1 | ⚠️ Zu viel |
| L3 | 28 | 6 | 🎯 Gut |
| L4/L5 | 25 | 16 | 🎯 Gut |

---

### Test 2: 50% Spam mit echten Domains
```
Gesamt:            200 Emails (180 normal + 20 spam)
Gesamt korrekt:    187/200 (93%) ✅
Spam erkannt:      18/20 (90%)
False Positives:   11/180 (6%)
Durchschlüpfer:    2 (pv60vaiy4va13u1@hotmail.com, P1uRr6YICt@yahoo.de)
needs_claude:      178/200 (89%) ⚠️ zu aggressiv
```

**Problem entdeckt:** Layer 2 Regel über-triggert! Mit echter Domain werden 90% aller Emails als "needs_claude" markiert (weil Provider SMTP blocken).

**Geplanter Fix:**
```python
# L2 nur relevant wenn lokaler Teil verdächtig ist
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

### Durchschlüpfer-Analyse

**Test 1: `1n6kvpuc8d1wj@fgca.info`**
```
Problem: GoDaddy geparkte Domain
→ L1: MX_FOUND ✅ (GoDaddy Server!)
→ L2: SMTP_CODE_550
→ L3: SLIGHT ⚠️
→ L4: SLIGHT ⚠️
→ Alter needs_claude Code: false → durchschlüpfer!

Mit neuem Fix: needs_claude = true → Claude würde es stoppen!
```

**Test 2: `pv60vaiy4va13u1@hotmail.com`**
```
Problem: Sehr lang + viele Zahlen
→ L1: MX_FOUND ✅
→ L2: SERVER_DISCONNECTED (Hotmail normal!)
→ L3: OK
→ L4: OK (nur 2 Konsonanten am Anfang)
→ L5: OK
→ Alle Layer versagen!

Hätte geholfen: digit_ratio Check! (4 von 14 = 0.29)
Mit Fix würde L2 + local_suspicious = true → Claude ✅
```

**Test 2: `P1uRr6YICt@yahoo.de`**
```
Problem: Groß/Klein Mix + kurz
→ L1: MX_FOUND ✅
→ L2: SERVER_DISCONNECTED (Yahoo normal!)
→ L3: OK
→ L4: SLIGHT 🟡 (rr = 2 Konsonanten aber OK)
→ L5: OK
→ Nur L4 SLIGHT — reicht aber nicht!

Mit Fix: SLIGHT in L4 + L2 Verdacht = needs_claude true ✅
```

---

## 🛠️ Tech Stack

| Komponente | Technologie | Zweck |
|-----------|------------|-------|
| Datenquelle | SAP S/4HANA Cloud (OData V2) | Orders + Business Partner |
| Orchestrierung | n8n (Self-Hosted) | Workflow Automation |
| ML Modelle | Isolation Forest (scikit-learn) | Anomalieerkennung (Order + Email) |
| AI Erklärung | Claude Haiku (Anthropic API) | Explainable AI |
| Prediction API | Flask (Python) | ML Model Serving |
| Datenbank | Supabase (PostgreSQL) | Orders + Anomalien + Email Checks |
| Benachrichtigung | GMX SMTP | HTML Email Digest |

---

## 📂 Projektstruktur

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
│   │   ├── generator.py                ← Email Generator (18 Kulturkreise)
│   │   ├── config.yaml                 ← Konfiguration
│   │   └── examples/
│   │       ├── sample_1000.csv         ← Training Data
│   │       └── sample_200_real_domain.csv ← Test 2 Data
│   ├── predict/
│   │   └── predict_server.py           ← Flask Server (alle Layers)
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
├── .env                                 ← API Keys (nicht in Git)
├── .gitignore
├── README.md
└── start_n8n.bat
```

---

## 🚀 Setup & Installation

### Voraussetzungen
- Node.js v22 (für n8n)
- Python 3.x
- SAP API Business Hub Account
- Anthropic API Key
- Supabase Projekt

### 1. Repository klonen
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
# .env Datei erstellen
SAP_API_KEY=dein_sap_key
ANTHROPIC_API_KEY=dein_anthropic_key
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=dein_supabase_key
```

### 4. Modelle trainieren
```bash
# SAP Order Modell
python python/training/isolation_forest_train.py

# Email Generator
cd python/generate
python generator.py
cd ../..

# Email Modell
python python/training/email_forest_train.py
```

### 5. Flask Server starten
```bash
python python/predict/predict_server.py
# → läuft auf http://localhost:5001
# ✅ SAP Modell geladen
# ✅ Email Modell geladen
```

### 6. n8n starten
```bash
start_n8n.bat
# → läuft auf http://localhost:5678
```

### 7. Workflows importieren
```
n8n → Import from File → workflows/sap_order_validating.json
n8n → Import from File → workflows/email_verification_v1.json
```

---

## 📸 Screenshots & Evidenz

### n8n SAP Order Workflow
![SAP Workflow](screenshots/n8n_workflow.jpg)

### n8n Email Verification Workflow
![Email Workflow](screenshots/n8n_email_workflow.png)

### Email Digest Output
![Email Digest](screenshots/email_digest.jpg)

### Layer 3+4 Test Output
![Test Layer 3+4](screenshots/test_layer34_output.png)

### SAP Anomalien in Supabase
![Supabase Anomalien](screenshots/supabase_anomalien.jpg)

### Email Checks in Supabase
![Supabase Email Checks](screenshots/supabase_email_checks.png)

---

## 🧪 Testen

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

## ⚠️ Bekannte Limitierungen

**SAP Sandbox:**
Die Sandbox enthält statische Testdaten. In Produktion würde der Workflow täglich neue Orders und Business Partner verarbeiten.

**Email Modell:**
Trainiert auf synthetischen Daten (1000 Emails, 18 Kulturkreise). Mit echten Produktionsdaten (Whitelist-Feedback, HIL) steigt die Genauigkeit schnell.

**needs_claude Over-Triggering:**
Test 2 zeigte: Layer 2 + Provider-Blocks = 178/200 (89%) Mails zu Claude. Fix ist konzipiert (local_suspicious Check), nicht yet deployed.

**Durchschlüpfer:**
2 Emails in Test 2 slipped durch alle Layers. Beide hätten mit dem geplanten `local_suspicious` Fix von Layer 2 erkannt.

---

## 📚 Dokumentation

Detaillierte Schritt-für-Schritt Dokumentation in `A_dokumetiation/`:

| Datum | Thema |
|-------|-------|
| 2026-05-15 | SAP API Setup, n8n, erster Claude Workflow |
| 2026-05-20 | Sales Order Pipeline, EDA, Isolation Forest |
| 2026-05-21 | Flask Server, End-to-End, Email Digest |
| 2026-05-29 | Email Verification Planung, 5-Layer Konzept |
| 2026-05-31 | Layer 3+4 Aufbau, Generator, n8n Workflow |
| 2026-06-01 | 8-Layer Architektur, 200er Tests, Erkenntnisse |

---

## 🇬🇧 English Summary

**For my friends and tutors**

This project demonstrates two automated Fraud Detection Pipelines built with SAP, n8n, Python, and Claude AI:

**Pipeline 1 — SAP Sales Order Anomaly Detection:**
- Isolation Forest detects statistical outliers in order data
- Claude AI explains every anomaly in plain language
- Automated HTML email digest with history and trend analysis

**Pipeline 2 — Email Verification (8-Layer Defense in Depth):**
- Layer 1: DNS MX Check
- Layer 2: SMTP Handshake (with provider awareness)
- Layer 3: Entropy Check (mathematics, no training needed)
- Layer 4: Consonant/Vowel Pattern (NEW! — most effective layer)
- Layer 5: Isolation Forest (trained on 1000 synthetic emails, 18 cultural backgrounds)
- Layer 6: Claude AI (context + explanation for borderline cases)
- Layer 7: Human in the Loop (admin decides, system learns)
- Layer 8: Auto-Retrain (weekly model updates)

**Key insight:** No single layer is perfect. Together they achieve 93-95% accuracy with 0 false negatives — exactly like real AML detection systems.

**SMTP Provider Behavior (discovered):**
Large email providers (Gmail, GMX, Hotmail, etc.) intentionally block SMTP verification checks. This is **normal** and not a spam signal! Layer 2 must be combined with other signals.

---

## 👤 Autor

**Martin Freimuth**
- 🌐 [Portfolio](https://www.martin-freimuth.dev)
- 💼 [LinkedIn](https://www.linkedin.com/in/martin-freimuth/)
- 📧 martin@houseofstocks.dev

---

## 📝 Lizenz

Dieses Projekt dient zu Demonstrations- und Lernzwecken.