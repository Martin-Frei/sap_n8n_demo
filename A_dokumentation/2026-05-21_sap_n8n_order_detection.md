# SAP × n8n × Claude — Tag 5 Dokumentation
## 21. Mai 2026 — Flask Integration, Pipeline End-to-End, Email Digest

*Fortsetzung der Gesamtdokumentation vom 20.05.2026*

---

## 🎯 Tagesziel

Den am Vortag geplanten Flask Prediction Server aufbauen, mit n8n verbinden und die komplette Pipeline end-to-end zum Laufen bringen — inklusive Email Digest mit Historie und Häufungsanalyse.

---

## 📅 Tag 5 — Mittwoch 21. Mai 2026

### 1. Flask Prediction Server aufgebaut

**Datei:** `python/predict/predict_server.py`

Flask ist wie Django — nur eine Datei statt viele:

```
Django:  views.py + urls.py + settings.py + models.py
Flask:   predict_server.py — fertig
```

**Drei Routen implementiert:**

| Route | Methode | Funktion |
|-------|---------|----------|
| `/health` | GET | Server + Modell Status prüfen |
| `/predict` | POST | Neue Orders auf Anomalien prüfen |
| `/retrain` | POST | Modell mit neuen Daten neu trainieren |

**Starten:**
```bash
cd C:\Users\tsinn\VSCode\Repos\sap_n8n_demo
venv_sap\Scripts\activate
python python/predict/predict_server.py
→ läuft auf http://localhost:5001
```

**Setup — drei Terminals parallel:**
```
Terminal 1: n8n Server      → localhost:5678
Terminal 2: Flask Server    → localhost:5001
Terminal 3: Entwicklung     → git, python scripts
```

**Wichtige Design-Entscheidungen:**
- Modell wird beim Serverstart geladen (einmalig) → predict() läuft in Millisekunden
- Unbekannte Kunden/User bekommen `-1` als Encoding → werden automatisch als verdächtig eingestuft
- Risiko Level wird automatisch berechnet: Score < -0.1 = KRITISCH, < -0.05 = VERDÄCHTIG, sonst PRÜFEN

---

### 2. n8n → Flask Verbindung (Content-Type Kampf)

**Das schwierigste Problem des Tages.** Mehrere Fehler nacheinander:

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| ECONNREFUSED | localhost vs 127.0.0.1 | URL auf `http://127.0.0.1:5001/predict` geändert |
| 415 Unsupported Media Type | Content-Type Header leer | Header über "Using Fields" statt JSON konfiguriert |
| `"body": { "": "" }` | Body als Parameter statt Raw | Body Content Type auf "Raw" + application/json |
| 50 einzelne Requests statt 1 | n8n sendet jedes Item einzeln | Settings → "Execute Once" → AN |
| 0 Anomalien bei 50 Orders | Orders sind normal, kein Fehler | Modell ist korrekt — PowerShell Test bestätigt |

**Finale funktionierende Konfiguration:**
```
Method: POST
URL: http://127.0.0.1:5001/predict
Send Headers: AN (Using Fields)
  → Content-Type: application/json
Send Body: AN
  → Body Content Type: Raw
  → Content Type: application/json
  → Body: {{ JSON.stringify($input.all().map(item => item.json)) }}
Settings: Execute Once → AN
```

---

### 3. Isolation Forest Validierung per PowerShell

Da die echten SAP Sandbox Orders "normal" waren (0 Anomalien), wurde das Modell mit Testdaten validiert:

```powershell
$result = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:5001/predict" -ContentType "application/json" -Body '[
  {"sales_order":"TEST1","customer_id":"FAKE_CUSTOMER","net_amount":500000,"created_by":"UNKNOWN_USER"},
  {"sales_order":"TEST2","customer_id":"17100001","net_amount":0.01,"created_by":"CB9980000027"},
  {"sales_order":"TEST3","customer_id":"USCU_S16","net_amount":425000,"created_by":"S4TESTER"},
  {"sales_order":"TEST4","customer_id":"NORMAL_KUNDE","net_amount":5000,"created_by":"CB9980000065"}
]'
```

**Ergebnis:**
```
TEST1: FAKE_CUSTOMER + 500k USD     → KRITISCH  (Score: -0.179)
TEST2: 17100001 + 0.01 USD          → VERDÄCHTIG (Score: -0.085)
TEST3: USCU_S16 + 425k USD          → KRITISCH  (Score: -0.110)
TEST4: NORMAL_KUNDE + 5000 USD      → VERDÄCHTIG (Score: -0.051)
```

**Erkenntnis:** Das Modell erkennt korrekt:
- Unbekannte Kunden → verdächtig
- Extreme Beträge (zu hoch oder zu niedrig) → verdächtig
- Kombination aus beidem → kritisch

---

### 4. Inkrementelles Laden funktioniert

**Problem gelöst:** Supabase Node gab bei leerer Tabelle 0 Items → Workflow stoppte.

**Lösung:** `Always Output Data: AN` im Supabase Node.

**Datum-Filter Logik:**
```
Lauf 1: Tabelle leer → Fallback 2016-01-01
Lauf 2: MAX(creation_date) = 2016-09-16 → Filter ab 2016-09-17
Lauf 3: MAX(creation_date) = 2016-10-04 → Filter ab 2016-10-05
→ Keine Duplikate, jede Order wird genau einmal verarbeitet
```

**SAP Datum ohne Uhrzeit Problem:**
```
SAP gibt: 2016-09-16T00:00:00
→ gt (greater than) holt denselben Tag nochmal
→ Lösung: +1 Tag draufrechnen + ge (greater or equal)
```

**Ergebnis nach mehreren Läufen:**
```sql
SELECT COUNT(*), MIN(creation_date), MAX(creation_date) FROM sap_sales_orders;
→ 800 Orders, 2016-08-17 bis 2016-11-02
```

---

### 5. Claude Integration — Ein Call für alle Anomalien

**Kosten-Optimierung:** Statt 25 einzelne Claude Calls → 1 Call mit allen Anomalien.

```
Vorher:  25 Anomalien = 25 Claude Calls = teuer + Rate Limit
Jetzt:   25 Anomalien = 1 Claude Call    = 25x günstiger
```

**Prompt-Struktur:**
```
Du bist ein Fraud Detection Experte.
Analysiere diese X auffälligen SAP Sales Orders auf Deutsch:

Order: 1343 | Kunde: USCU_S14 | Betrag: 271377 USD | Score: -0.024
Order: 1512 | Kunde: USCU_S14 | Betrag: 265029 USD | Score: -0.046
...

Gib für jede Order:
1. Warum auffällig (1 Satz)
2. Empfohlene Maßnahme (1 Satz)
3. Risiko Level: KRITISCH / VERDÄCHTIG / PRÜFEN
```

---

### 6. Claude Response Parsing + Supabase Speicherung

**Claude Antwort aufsplitten** — Code Node parsed den Markdown Text:

```javascript
// Text nach "## Order" splitten
const orderBlocks = claudeText.split('## Order ').filter(b => b.trim());

// Für jeden Block: Order ID, Risiko Level, Flask Daten matchen
const flaskOrder = flaskData.find(a => String(a.sales_order) === salesOrder);
```

**Datenbank-Ergebnis:**
```sql
SELECT COUNT(*) FROM sap_order_anomalies;
→ 9 Anomalien gespeichert
```

**Beispiel gespeicherter Eintrag:**
```json
{
  "id": 1,
  "sales_order": "1343",
  "customer_id": "USCU_S14",
  "net_amount": 271377.00,
  "anomaly_score": -0.0242,
  "claude_analyse": "Der negative Anomalie-Score deutet auf ein Muster hin, 
                     das signifikant vom normalen Verhalten abweicht...",
  "risiko_level": "VERDÄCHTIG",
  "detected_at": "2026-05-21T10:18:24"
}
```

---

### 7. Email Digest mit Historie und Häufungscheck

**Architektur der Digest Pipeline:**
```
anomalie_safe_supabase
        ↓
historie_orders (Supabase → sap_sales_orders)
        ↓
historie_anomalien (Supabase → sap_order_anomalies)
        ↓
js_digest_for_email (Code Node → HTML bauen)
        ↓
Send Email (GMX SMTP)
```

**Digest Inhalt:**

| Sektion | Daten |
|---------|-------|
| 📊 Datenbestand | 800 Orders, 78 Tage, 10.3 Orders/Tag |
| 📈 Anomalie Historie | 9 Anomalien, 1.13% Rate |
| Verteilung | KRITISCH: 0, VERDÄCHTIG: 6, PRÜFEN: 3 |
| 🔥 Top 5 Anomalie Tage | 21.05.2026: 9 Anomalien |
| 🔍 Häufungscheck | ✅ Normal (9 heute, Schnitt 9.0) |
| 🚨 Letzte 10 Anomalien | Detail mit Order, Kunde, Betrag, Score, Risiko |

**Fehler und Lösungen beim Digest:**

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| 14.400 Anomalien statt 9 | Supabase Abfrage pro Item wiederholt | Execute Once: AN |
| "Node hasn't been executed" | Workflow stoppt bei 0 Anomalien | Always Output Data + try/catch |
| 5500 Items statt Digest | Standard-Template Code im Node | Digest Code eingefügt |
| GMX 450 Rate Limit | 50 einzelne Emails vorher gesendet | Execute Once + 15 Min warten |
| "Sender address not allowed" | From ≠ SMTP User | From = tsinntal@gmx.de |

---

## 🏗️ Finale Workflow Architektur

```
When clicking 'Execute workflow'
        ↓
Supabase (letztes Datum holen, Always Output Data)
        ↓
js_datum_2016_erzeugen (+1 Tag oder Fallback)
        ↓
order_request_2000 (SAP OData, dynamischer $filter)
        ↓
JS_daten_für_supabase_aubereiten
        ↓                    ↓
Create a row             http_request_flask
(Supabase orders)        (Execute Once, 127.0.0.1:5001)
                              ↓
                         llm_prompt (alle Anomalien → 1 Prompt)
                              ↓
                         HTTP Request (Claude API)
                              ↓
                         claude_parsen (Markdown → einzelne Orders)
                              ↓
                         anomalie_safe_supabase (Always Output Data)
                              ↓
                         historie_orders (Execute Once)
                              ↓
                         historie_anomalien (Execute Once)
                              ↓
                         js_digest_for_email (HTML Report)
                              ↓
                         Send Email (Execute Once)
```

---

## 📊 Aktueller Datenstand

```sql
-- Orders
SELECT COUNT(*), MIN(creation_date), MAX(creation_date) FROM sap_sales_orders;
→ 800 Orders | 2016-08-17 bis 2016-11-02

-- Anomalien
SELECT COUNT(*), 
  COUNT(CASE WHEN risiko_level='KRITISCH' THEN 1 END) as kritisch,
  COUNT(CASE WHEN risiko_level='VERDÄCHTIG' THEN 1 END) as verdaechtig,
  COUNT(CASE WHEN risiko_level='PRÜFEN' THEN 1 END) as pruefen
FROM sap_order_anomalies;
→ 9 Anomalien | 0 KRITISCH | 6 VERDÄCHTIG | 3 PRÜFEN
```

---

## 📚 Wichtigste Lernpunkte Tag 5

### Flask
```
✅ Flask = Django in einer Datei
✅ @app.route() = urls.py + views.py kombiniert
✅ request.json = request.data in Django
✅ jsonify() = JsonResponse() in Django
✅ debug=True = auto-reload bei Änderungen
✅ host='0.0.0.0' = von außen erreichbar
```

### n8n HTTP Request
```
✅ Content-Type muss über "Using Fields" gesetzt werden
✅ Body als "Raw" + application/json
✅ Execute Once für Batch-Verarbeitung
✅ 127.0.0.1 statt localhost in n8n
✅ Always Output Data wenn Node leer sein könnte
```

### Kostenoptimierung
```
✅ Alle Anomalien in einem Claude Call statt einzeln
✅ Flask predict() ist kostenlos (lokal)
✅ Nur Anomalien an Claude → 95% API-Kosten gespart
```

### Datenfluss
```
✅ $input.all() → Daten vom direkten Vorgänger
✅ $("node_name") → Daten von beliebigem Node
✅ Execute Once → verhindert Vervielfachung
✅ Always Output Data → Workflow stoppt nicht bei 0 Items
```

---

## 📂 Aktualisierte Projektstruktur

```
sap_n8n_demo/
├── .env
├── .gitignore
├── README.md
├── start_n8n.bat
├── A_dokumetiation/
│   ├── 2026-05-15_sap_n8n_claude_fraud.md
│   ├── 2026-05-20_sap_n8n_order_detection.md
│   ├── 2026-05-21_sap_n8n_order_detection.md
│   └── Startcode_batDatei.md
├── data/
│   ├── binary-data (1).csv
│   └── sap_order_raw.csv
├── models/
│   ├── sap_isolation_forest.pkl
│   ├── label_encoder_customer.pkl
│   └── label_encoder_user.pkl
├── python/
│   ├── requirements.txt
│   ├── predict/
│   │   └── predict_server.py
│   ├── training/
│   │   └── isolation_forest_train.py
│   └── utils/
│       └── sales_order_eda.py
├── venv_sap/            
└── workflows/
    ├── sap_claude_analyse_v1.json
    └── sap_order_validating.json
```

---

## 🚧 Noch offen

```
→ Email Digest versenden (GMX Rate Limit abwarten)
→ Workflow B: Wöchentliches Retraining automatisieren
→ Workflow 2: Email Validation Pipeline (DNS/SMTP Check)
→ Schedule Trigger statt Manual Trigger
→ Deployment auf Railway
→ README.md aktualisieren für Joachim
```

---

## 💡 Nächste Schritte

```
1. Email Digest versenden (GMX Rate Limit abgelaufen)
2. README.md aktualisieren (für Joachim Uhl sichtbar auf GitHub)
3. Andreas Moser Update: "Workflow läuft end-to-end"
4. Workflow B: Retraining per Schedule Trigger
```

---

## 👥 Kontakte Update


**Andreas** — Enterprise Architect
- SM21 Use Case bleibt als Referenz (RFC-basiert)
- Alternative Sales Order Anomalie Detection umgesetzt
- Update ausstehend: "Pipeline läuft end-to-end"

---

*Dokumentiert am 21.05.2026 — SAP × n8n × Flask × Isolation Forest × Claude Pipeline*