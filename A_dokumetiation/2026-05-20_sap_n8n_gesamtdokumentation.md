# SAP × n8n × Claude — Fraud Detection & Anomalie Detection
## Vollständige Projektdokumentation — 14.–20. Mai 2026

---

## 🎯 Projektziel

Zwei produktionsnahe Workflows aufbauen:

1. **SAP Fraud Detection** — Email-Adressen aus SAP auf Betrug prüfen
2. **SAP Sales Order Anomalie Detection** — Bestellmuster mit Isolation Forest analysieren

Beide Workflows nutzen SAP OData APIs, n8n als Orchestrierung, Claude AI für Explainable AI, Supabase als Datenbank und Email für Reporting.

---

## 🏗️ Technischer Stack

```
SAP API Business Hub (Sandbox)  → Datenquelle (OData V2)
n8n (lokal, v2.8.4)             → Workflow Orchestrierung
Claude Haiku (Anthropic API)    → AI Fraud Detection / Explainable AI
Supabase (PostgreSQL)           → Datenspeicherung
Isolation Forest (sklearn)      → ML Anomalie Detection
Flask                           → Prediction Server (geplant)
GMX SMTP                        → Email Benachrichtigung
Node.js v22.22.3 (via fnm)      → n8n Runtime
Python 3.x + venv_sap           → ML Pipeline
VSCode                          → Entwicklungsumgebung
GitHub                          → Versionskontrolle
```

---

## 📅 Tag 1 — Donnerstag 14. Mai 2026 (Vatertag)

### SAP API Business Hub Account
- Account auf api.sap.com angelegt
- Produkt: SAP S/4HANA Cloud Public Edition (861 APIs)
- API: Business Partner (A2X) — OData V2
- Ersten API Call im Browser: A_AddressEmailAddress → echte Testdaten
- API Key in .env gesichert

### n8n Installation

**Fehler:** Node.js v25.9.0 nicht unterstützt
```
Your Node.js version 25.9.0 is currently not supported
Please use: >=20.19 <= 24.x
```

**Lösung:** fnm (Fast Node Manager) mit Node v22 parallel installiert
```bash
fnm install 22
```

**Fehler:** fnm Shell Setup schlägt fehl (Windows Security Policy)
```
error: We can't find the necessary environment variables
```

**Finale Lösung — Batch Datei:**
```batch
@echo off
"C:\Users\tsinn\AppData\Roaming\fnm\node-versions\v22.22.3\installation\node.exe"
"C:\Users\tsinn\AppData\Local\npm-cache\_npx\...\node_modules\n8n\bin\n8n"
```

**Lektion:** start_n8n.bat startet n8n mit Node v22, Standard bleibt v25 für React. Kein Konflikt, kein Umstellen.

### Erster Workflow — SAP Mock + Claude

**Nodes gebaut:**
```
Manual Trigger → Code in JavaScript (SAP Mock) → claude_code → HTTP Request (Claude API)
```

**Fehler:** API Key direkt im HTTP Request Node hardcoded
```json
"x-api-key": "sk-ant-api03-..."
```
→ Key landete im JSON Export → auf GitHub gepusht!

**Sofort-Maßnahme:** Key deaktiviert, neuer Key erstellt

**Lektion:** Secrets gehören NIE in den Code — immer n8n Credentials nutzen. Credentials werden verschlüsselt in n8n's interner Datenbank gespeichert und erscheinen nicht im JSON Export.

**Fehler:** Claude API "Invalid URL"

**Ursache:** Falscher Modell-Name

**Lösung:** Exakter Model-String: `claude-haiku-4-5-20251001`

**Fehler:** `{{ $json }}` funktioniert nicht in JSON Body

**Lösung:** Body auf Raw umstellen mit `{{ JSON.stringify($json) }}`

**Ergebnis:** Claude analysiert SAP Mock-Daten erfolgreich auf Deutsch.

### GitHub Repository
- sap_n8n_demo angelegt (Private)
- .gitignore mit .env
- Workflow als JSON exportiert
- .env nicht auf GitHub (verifiziert)

---

## 📅 Tag 2 — Freitag 15. Mai 2026

### Echter SAP API Call

SAP Sandbox war Vatertag down — heute wieder verfügbar.

```
Method: GET
URL: .../API_BUSINESS_PARTNER/A_AddressEmailAddress?$top=5
Authentication: Generic Credential Type → Header Auth
```

**Ergebnis:** 5 echte Business Partner Email-Adressen in n8n!

### Fraud Detection Prompt

Claude als Fraud Detection Experte:
```
Du bist ein Fraud Detection Experte.
Analysiere diese SAP Business Partner Email auf Deutsch:
Antworte mit: UNAUFFÄLLIG / VERDÄCHTIG / PRÜFEN
Begründung in 2-3 Sätzen.
```

**Ergebnis:** Alle 5 Kontakte als VERDÄCHTIG eingestuft — Domains wie 10100001.com sind tatsächlich verdächtig!

### Security Fix — Credentials richtig nutzen

```
Authentication Prinzip:
Credential  = Personalausweis (einmal hinterlegt, n8n zeigt automatisch vor)
Header      = Visitenkarte (zusätzliche Info, z.B. anthropic-version)
Body        = der eigentliche Brief (Prompt an Claude)
```

### Email Report

**Fehler:** 5 SAP Kontakte → 5 separate Emails

**Lösung:** Code Node sammelt alle Ergebnisse in eine HTML Email:
```javascript
const zusammenfassung = items.map((item, index) => {
  return `<h3>🔍 Kontakt ${index + 1}</h3><p>${text}</p>`;
}).join('');
```

### Split Out + Merge für Datenbank

**Fehler:** SAP gibt alle Daten als ein Item, Claude gibt 5 separate Items

**Lösung:** Split Out Node zwischen SAP und claude_code:
```
SAP → Split Out (d.results) → claude_code → HTTP Claude → Merge (Input 1)
SAP → Split Out ──────────────────────────────────────→ Merge (Input 2)
```

### Supabase Integration

Tabelle fraud_detection_results angelegt. Wichtige Entscheidung: Supabase API statt direkter PostgreSQL Verbindung — Passwort Reset hätte bestehende Django SPV2 Verbindungen gebrochen.

**Ergebnis:** Erste Fraud Detection Ergebnisse in Supabase gespeichert.

---

## 📅 Tag 3 — Sonntag 18. Mai 2026 (eigenständige Arbeit)

### Architektur-Planung

**2-Wege-Strategie für die Pipeline selbstständig entwickelt:**

**Workflow A — Live-Check (täglich):**
1. n8n holt jüngstes Datum aus Supabase
2. SAP Abfrage mit dynamischem Datumsfilter
3. Upsert an Supabase (sales_order als Match-Spalte)
4. Isolation Forest predict() mit "eingefrorenem" Modell (joblib.load)
5. Anomalien → Claude → Email Digest

**Workflow B — Retraining (wöchentlich):**
1. Alle Daten aus Supabase laden
2. Isolation Forest neu trainieren (model.fit)
3. Modell überschreiben (joblib.dump)

### JavaScript Datenaufbereitung (eigenständig gelöst)

Drei kritische Probleme selbstständig gelöst:

**1. SAP Datums-Konvertierung:**
```javascript
// SAP: /Date(1471392000000)/  →  ISO: 2016-08-17T00:00:00.000Z
const milliSeconds = parseInt(order.CreationDate.replace(/\/Date\((\d+)\)\//, '$1'));
isoDate = new Date(milliSeconds).toISOString();
```

**2. Kunden-ID Extraktion (Sold-to Party):**
```javascript
const soldToPartner = order.to_Partner?.results?.find(p => p.PartnerFunction === 'SP');
const customerId = soldToPartner ? soldToPartner.Customer : (order.SoldToParty || "Unbekannt");
```

**3. Struktur-Symmetrie (PostgreSQL Batch-Schutz):**
```javascript
// Jedes Feld existiert IMMER — verhindert "All object keys must match" Fehler
sales_order: order.SalesOrder || null,
delivery_status: order.OverallTotalDeliveryStatus || null
```

### Daten-Pipeline Fehler & Lösungen

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| Nur 149 Zeilen erhalten | Zweiter Flow hat Prozess unterbrochen | Prozesse atomar halten, try-catch nutzen |
| Fehler in Flow 2 | Race Condition / Rate Limiting | Verzögerung (sleep) zwischen Flows |
| API-Limits | RLS-Policy oder Payload-Limits | Count prüfen, Daten verifizieren |

**Lektion:** Isolation vor Integration — Flow 1 muss stabil laufen bevor Flow 2 drangehängt wird.

### SQL Setup

```sql
CREATE TABLE sap_sales_orders (
    sales_order VARCHAR(50) PRIMARY KEY,
    order_type VARCHAR(10),
    organization VARCHAR(10),
    customer_id VARCHAR(50),
    net_amount NUMERIC(12, 2),
    creation_date TIMESTAMP WITH TIME ZONE,
    currency VARCHAR(5),
    created_by VARCHAR(50),
    delivery_status VARCHAR(5)
);
```

**Design-Entscheidungen:**
- VARCHAR statt TEXT (sauberer für SAP Daten)
- NUMERIC(12,2) für Beträge (nicht FLOAT — Rundungsfehler!)
- sales_order als String (SAP führende Nullen, alphanumerische Zeichen)

---

## 📅 Tag 4 — Dienstag 20. Mai 2026

### SAP Sandbox Datenkonsistenz-Problem

**Entdeckt:** Sales Order API und Business Partner API verwenden unterschiedliche Test-IDs

```
Sales Order API:        SoldToParty = 17100001
Business Partner API:   Customer = 202, 203...
→ Kein direkter Join möglich!
```

**Getestet:**
- A_Customer gibt IDs: 202, 203...
- A_SalesOrder gibt SoldToParty: 17100001
- Keine Überschneidung in der Sandbox

**In Produktion:** Bei einem echten SAP System wären alle IDs konsistent (Sales Order → Customer → Business Partner → Email).

**Workaround:** Zwei unabhängige Pipelines — Claude bewertet beide Ergebnisse im Digest.

### 12.000 Sales Orders in Supabase geladen

**Fehler:** SAP Sandbox limitiert auf 500 Rows pro Request (trotz $top=1000)

**Lösung:** Manuelle Pagination mit $skip:
```
Request 1: $top=500&$skip=0     → 500 Rows
Request 2: $top=500&$skip=500   → 1000 Rows
...
Bis 12.000 Rows komplett
```

**Fehler:** "duplicate key value violates unique constraint"

**Ursache:** Supabase Node hat kein Upsert in dieser n8n Version

**Lösung:** DELETE FROM sap_sales_orders → dann Create (Insert)

**Ergebnis:** 12.000 Rows, 53 Tage (17.08.2016 – 30.11.2016), ~240 Orders/Tag

### Explorative Datenanalyse (EDA)

**Script:** python/utils/sales_order_eda.py

**Erkenntnisse:**
```
📊 2000 Rows (erster Batch), 9 Spalten
💰 net_amount: Min 0.00, Mean 27.233, Max 425.755, Std 51.984
⚠️ 49 fehlende delivery_status Werte
⚠️ Nur 1x Status "B" vs 1950x "C"
⚠️ net_amount = 0.00 existiert
⚠️ 43 verschiedene Kunden, nur 1 Organization (kein Feature)
```

**Fehler:** FileNotFoundError — sap_oder_raw.csv vs sap_order_raw.csv

**Lektion:** Tippfehler in Dateinamen immer prüfen!

**Fehler:** pandas Installation — ModuleNotFoundError: pkg_resources

**Lösung:** pip install setuptools wheel zuerst, dann requirements ohne fixe Versionen

### Isolation Forest Training

**Script:** python/training/isolation_forest_train.py

```python
model = IsolationForest(
    contamination=0.05,    # 5% Anomalien erwartet
    n_estimators=100,      # 100 Bäume
    random_state=42
)
```

**Ergebnis:**
```
Normal:   1900 Orders
Anomalie: 100 Orders (5%)

TOP Anomalien:
→ 425.755 USD (USCU_S16) — höchster Betrag im Datensatz
→ 402.532 USD (USCU_S16) — wiederholt auffällig
→ 387.050 USD (USCU_S17) — Cross-Kunde Muster
→ 353.50 USD  (17100001) — anderer Kundentyp erkannt!
→ 52.65 USD   (17100001) — Isolation Forest erkennt Formatunterschied
```

**Spannend:** Kunde 17100001 fällt auf — nicht wegen Betrag sondern wegen anderem Kundenformat (numerisch vs USCU-Format). Isolation Forest erkennt strukturelle Unterschiede!

**Modell gespeichert:**
```
models/sap_isolation_forest.pkl
models/label_encoder_customer.pkl
models/label_encoder_user.pkl
```

### n8n Python Integration

**Fehler:** Python Code Node → "Virtual environment is missing"
```
Python runner unavailable: Virtual environment is missing from this system
```

**Ursache:** n8n Python Runner braucht extra Setup

**Geplante Lösung:** Flask Prediction Server
```
Terminal 1: n8n auf localhost:5678
Terminal 2: Flask auf localhost:5001
n8n → HTTP Request → Flask → Anomalien zurück → Claude → Digest
```

### 3-Layer Fraud Detection Architektur (mit Tutorin erarbeitet)

**Layer 1 — Technische Validierung:**
```
MX Record prüfen → existiert die Domain?
SMTP Handshake   → existiert der Account?
```

**Layer 2 — ML (Isolation Forest):**
```
Features: Domain existiert? (0/1), Account existiert? (0/1),
          Domain numerisch? (0/1), Domain Länge, TLD Risiko
Entscheidung: ANOMALIE oder NORMAL
```

**Layer 3 — Claude Erklärung (Explainable AI):**
```
Nur für Anomalien aus Layer 2:
→ warum verdächtig?
→ welche Kombination macht es auffällig?
→ Handlungsempfehlung
```

**Kostenersparnis:**
```
Ohne ML: 1000 Emails → 1000 Claude Calls → teuer
Mit ML:  1000 Emails → 50 Anomalien → 50 Claude Calls → 95% günstiger
```

---

## 🏗️ Finale Workflow Architektur

### Workflow 1 — SAP Fraud Detection (fertig)

```
Manual Trigger
    ↓
HTTP Request (SAP Business Partner Emails)
    ↓
Split Out (d.results)
    ↓                              ↓
claude_code + HTTP Claude    (SAP Rohdaten)
    ↓                              ↓
    └────────── Merge ─────────────┘
                   ↓
           ┌───────┴───────┐
           ↓               ↓
      Supabase         Code JS1
      (Insert)     (Zusammenfassung)
                           ↓
                      Send Email
```

### Workflow 2 — Sales Order Anomalie Detection (in Arbeit)

```
Workflow B (wöchentlich — Training):
    Supabase SELECT * → Python Isolation Forest → joblib.dump

Workflow A (täglich — Prediction):
    SQL: MAX(creation_date)
        ↓
    SAP: neue Orders ab nächstem Tag
        ↓
    Supabase: speichern
        ↓
    Flask API: predict() → Anomalien
        ↓
    Claude: nur Anomalien erklären
        ↓
    ┌───┴───┐
    ↓       ↓
Supabase  Email Digest
(anomalies)
```

---

## 📚 Wichtigste Lernpunkte

### Security
```
❌ API Keys NIE direkt in Nodes
❌ API Keys NIE im Code hardcoden
✅ n8n Credentials verwenden (verschlüsselt)
✅ .env für lokale Entwicklung
✅ .gitignore schützt .env und venv
```

### n8n Best Practices
```
✅ Separation of Concerns — ein Node, eine Aufgabe
✅ Code Nodes für Datentransformation
✅ Credentials für alle API Keys
✅ Workflow als JSON exportieren und versionieren
✅ Mock Daten für Entwicklung wenn API down
✅ Split Out für Array-Verarbeitung
✅ Merge für parallele Datenströme
```

### SAP OData
```
✅ Header exakt "APIKey" (Groß-/Kleinschreibung!)
✅ Sandbox manchmal down (Vatertag, Wochenende)
✅ Daten verschachtelt: d.results[n].Feldname
✅ Pagination mit $top und $skip nötig
✅ Sandbox limitiert auf 500 Rows pro Request
✅ Sandbox Daten nicht konsistent zwischen APIs
✅ SAP Datum: /Date(milliseconds)/ → ISO umrechnen
✅ PartnerFunction 'SP' = Sold-to Party
```

### Machine Learning
```
✅ Isolation Forest = unsupervised (keine Labels nötig)
✅ contamination = erwarteter Anteil Anomalien
✅ LabelEncoder für kategoriale Features
✅ decision_function() gibt Anomalie-Score
✅ Modell mit joblib speichern/laden
✅ Retraining wöchentlich um Drift zu vermeiden
✅ EDA vor dem Training — Daten verstehen!
✅ Isolation vor Integration — Flow 1 stabil bevor Flow 2
```

### PostgreSQL / Supabase
```
✅ VARCHAR statt TEXT für SAP Daten
✅ NUMERIC(12,2) für Beträge (nicht FLOAT!)
✅ BIGSERIAL für Auto-Increment IDs
✅ INDEX auf häufig gefilterte Spalten
✅ REFERENCES für Foreign Keys
✅ Struktur-Symmetrie: || null für Batch-Insert
✅ Keyset Pagination statt OFFSET für große Datenmengen
```

### Python Umgebung
```
✅ venv pro Projekt (venv_sap)
✅ requirements.txt ohne fixe Versionen
✅ setuptools + wheel vor pandas installieren
✅ Dateinamen exakt prüfen
```

---

## 🚧 Noch offen

```
→ Flask Prediction Server aufsetzen (predict_server.py)
→ n8n HTTP Request → Flask → Anomalien
→ Anomalien → Claude → Statement
→ sap_order_anomalies befüllen
→ Email Digest mit kombiniertem Report
→ Business Partner Email Validierung (MX/SMTP Layer)
→ Teams Benachrichtigung (Azure App Registration nötig)
→ Automatischer Schedule Trigger
→ Deployment auf Railway
→ Finaler Git Commit mit komplettem Workflow
```

---

## 📋 Nächste Schritte

```
1. pip install flask
2. predict_server.py schreiben + starten (localhost:5001)
3. n8n HTTP Request → localhost:5001/predict
4. Claude nur Anomalien erklären
5. sap_order_anomalies speichern
6. Email Digest
7. Workflow Export + Git Commit
8. Dokumentation für Joachim Uhl vorbereiten
```

---

## 📂 Projektstruktur

```
sap_n8n_demo/
├── .env                              ← API Keys (nie in Git!)
├── .gitignore
├── README.md
├── start_n8n.bat                     ← n8n mit Node v22 starten
├── A_dokumentation/
│   └── SAP_n8n_Claude_Projektdokumentation.md
├── data/
│   └── sap_order_raw.csv             ← SAP Export
├── models/
│   ├── sap_isolation_forest.pkl      ← trainiertes Modell
│   ├── label_encoder_customer.pkl
│   └── label_encoder_user.pkl
├── python/
│   ├── requirements.txt
│   ├── training/
│   │   └── isolation_forest_train.py
│   ├── predict/
│   │   └── predict_server.py         ← Flask (geplant)
│   └── utils/
│       └── sales_order_eda.py
├── venv_sap/                         ← Python Virtual Environment
└── workflows/
    ├── sap_fraud_detection_v1.json
    └── customer_validating.json
```

---

## 🔗 Wichtige Links

```
SAP API Hub:     https://api.sap.com
n8n lokal:       http://localhost:5678
Supabase SPV2:   https://supabase.com/dashboard/project/qxfenlowtcxcwapfznpb
Anthropic:       https://console.anthropic.com
GitHub Repo:     https://github.com/[username]/sap_n8n_demo
```

---

## 👥 Netzwerk & Kontakte

**Andreas** — Enterprise Architect & SAP Transformation Leader
- LinkedIn 1. Grades Kontakt
- Hat SM21 Systemlog-Digest Use Case vorgeschlagen (RFC-basiert)
- Positiver Austausch über Isolation Forest + Claude Ansatz
- Nächster Schritt: Ergebnis zeigen wenn Workflow komplett

**Adeena** — ML Tutorin
- Verstärkt ML Basics, Isolation Forest Vertiefung

**Irfana** — ML Tutorin
- SMTP Handshake als Validierungs-Layer vorgeschlagen

**Tanveer** — SUSI/Ollama Tutor
- Verstärkt lokale AI Entwicklung

---

*Dokumentiert am 20.05.2026 — SAP × n8n × Claude Fraud & Anomalie Detection Projekt*
