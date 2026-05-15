# SAP × n8n × Claude — Fraud Detection Workflow
## Projektdokumentation — 14./15. Mai 2026

---

## 🎯 Projektziel

Einen vollständigen, produktionsnahen Workflow aufbauen der:
1. Echte SAP Daten über die OData API abruft
2. Diese Daten mit Claude AI auf Fraud-Muster analysiert
3. Ergebnisse in einer PostgreSQL Datenbank (Supabase) speichert
4. Einen formatierten Report per Email versendet

---

## 🏗️ Technischer Stack

```
SAP API Business Hub (Sandbox)  → Datenquelle
n8n (lokal, v2.8.4)             → Workflow Orchestrierung
Claude Haiku (Anthropic API)    → AI Fraud Detection
Supabase (PostgreSQL)           → Datenspeicherung
GMX SMTP                        → Email Benachrichtigung
Node.js v22.22.3 (via fnm)      → n8n Runtime
VSCode                          → Entwicklungsumgebung
GitHub                          → Versionskontrolle
```

---

## 📅 Tag 1 — Donnerstag 14. Mai 2026 (Vatertag)

### Schritt 1: SAP API Business Hub Account
- Account auf `api.sap.com` angelegt
- Produkt gewählt: **SAP S/4HANA Cloud Public Edition**
- API gefunden: **Business Partner (A2X) — OData V2**
- Ersten erfolgreichen API Call im Browser gemacht:
  - Endpoint: `/A_AddressEmailAddress`
  - Response: Echte Testdaten mit Email-Adressen
- **API Key gesichert in `.env` Datei**

### Schritt 2: n8n Installation
**Problem:** `n8n` Befehl nicht gefunden
```
n8n : Die Benennung "n8n" wurde nicht als Name erkannt
```

**Ursache:** n8n noch nicht installiert

**Lösung:**
```bash
npm install -g n8n
```

**Problem 2:** Node.js v25.9.0 zu neu für n8n
```
Your Node.js version 25.9.0 is currently not supported
Please use: >=20.19 <= 24.x
```

**Ursache:** n8n unterstützt Node v25 noch nicht

**Lösung:** fnm (Fast Node Manager) installiert und Node v22 parallel eingerichtet:
```bash
winget install Schniz.fnm
fnm install 22
```

**Problem 3:** fnm Shell Setup schlägt fehl wegen Windows Security Policy
```
error: We can't find the necessary environment variables
```

**Finale Lösung — Batch Datei:**
```batch
@echo off
"C:\Users\tsinn\AppData\Roaming\fnm\node-versions\v22.22.3\installation\node.exe" 
"C:\Users\tsinn\AppData\Local\npm-cache\_npx\...\node_modules\n8n\bin\n8n"
```
→ `start_n8n.bat` — Doppelklick startet n8n mit Node v22, ohne Node v25 zu beeinflussen!

**Lernpunkt:** Node Version Manager erlaubt parallele Versionen — wichtig wenn verschiedene Projekte verschiedene Node Versionen brauchen.

### Schritt 3: n8n Setup
- Account angelegt (lokal)
- Kostenlose Community License Key angefordert
- Dashboard erreicht: `http://localhost:5678`

### Schritt 4: Erster Workflow — SAP Mock + Claude
**Nodes gebaut:**
1. `Manual Trigger` — startet den Workflow manuell
2. `Code in JavaScript` — simuliert SAP Daten (Mock)
3. `claude_code` — bereitet Claude API Body vor
4. `HTTP Request` — ruft Anthropic API auf

**Problem: Anthropic API Key direkt im Node hardcoded**

```json
"x-api-key": "sk-ant-api03-aVi4S0g..."
```

→ Key landet im JSON Export → landet auf GitHub → Sicherheitsproblem!

**Fehler dabei gemacht:**
- Key wurde exported und auf GitHub gepusht
- Sofort: Key deaktiviert, neuer Key erstellt

**Lernpunkt:** Secrets gehören NIE in den Code — immer in n8n Credentials oder `.env`

**Richtige Lösung:**
```
n8n → Credentials → Anthropic Account
→ verschlüsselt gespeichert
→ erscheint nicht im JSON Export
```

**Problem: Claude API "Invalid URL" Fehler**
```
Problem in node 'HTTP Request'
Invalid URL
```

**Ursache:** Falscher Modell-Name
```
claude-sonnet-4-20250514  ← existiert nicht exakt so
claude-haiku-4-5-20251001 ← korrekter Model-String
```

**Lernpunkt:** Modell-Namen exakt aus Anthropic Dokumentation kopieren!

**Problem: `{{ $json }}` in JSON Body funktioniert nicht**
```
Invalid expression
```

**Lösung:** Body auf `Raw` umstellen:
```
Body Content Type: Raw
Body: {{ JSON.stringify($json) }}
```

**Erster Erfolg:** Claude antwortet in n8n!
```
"Hallo! 👋 Wie geht es dir?"
```

### Schritt 5: Claude analysiert SAP Mock Daten
Claude Haiku analysiert Müller GmbH und Schmidt AG aus dem Mock:
- Strukturierte Analyse mit Tabellen
- Fehlende Daten identifiziert
- Empfehlungen gegeben

**Workflow bis hier:**
```
Manual Trigger → Code (SAP Mock) → claude_code → HTTP Request (Claude)
```

### Schritt 6: GitHub Repository
- Repository `sap_n8n_demo` angelegt
- `.gitignore` mit `.env` Eintrag
- Workflow als JSON exportiert: `sap_claude_analyse_v1.json`

**Projektstruktur:**
```
sap_n8n_demo/
├── .env                    ← API Keys (nie in Git!)
├── .gitignore
├── README.md
├── start_n8n.bat           ← n8n mit Node v22 starten
├── A_dokumentation/
└── workflows/
    └── sap_claude_analyse_v1.json
```

---

## 📅 Tag 2 — Freitag 15. Mai 2026

### Schritt 7: Echter SAP API Call in n8n

**SAP Sandbox war am Vortag (Vatertag) down** — heute wieder verfügbar.

Neuer HTTP Request Node für SAP:
```
Method: GET
URL: https://sandbox.api.sap.com/s4hanacloud/sap/opu/odata/sap/API_BUSINESS_PARTNER/A_AddressEmailAddress?$top=5
Authentication: Generic Credential Type → Header Auth
```

**Wichtige Erkenntnis:** SAP erwartet Header exakt `APIKey` — Groß-/Kleinschreibung wichtig!

**Erster echter SAP Response in n8n:**
```json
{
  "AddressID": "22820",
  "EmailAddress": "info@10100001.com",
  "Person": "",
  "IsDefaultEmailAddress": true
}
```

### Schritt 8: Fraud Detection Prompt

Claude bekommt den Auftrag als Fraud Detection Experte:
```
Du bist ein Fraud Detection Experte.
Analysiere diese SAP Business Partner Email auf Deutsch:

Email: ${partner.EmailAddress}
AddressID: ${partner.AddressID}
Person: ${partner.Person || 'Firmenkontakt'}

Antworte mit: UNAUFFÄLLIG / VERDÄCHTIG / PRÜFEN
Begründung in 2-3 Sätzen.
```

**Claude Ergebnis:**
```
VERDÄCHTIG

Die Domain "10100001.com" ist eine reine Zahlenkombination 
ohne erkennbaren Firmennamen – dies ist ein klassisches 
Merkmal von Fraud-Domains...
```

### Schritt 9: Email Report

**Problem:** 5 SAP Kontakte = 5 separate Emails

**Lösung:** Code Node der alle Ergebnisse zusammenfasst:
```javascript
const items = $input.all();
const zusammenfassung = items.map((item, index) => {
  const text = Array.isArray(content) ? content[0].text : content;
  return `<h3>🔍 Kontakt ${index + 1}</h3><p>${text}</p>`;
}).join('');
```

**Ergebnis:** Eine formatierte HTML Email mit allen 5 Analysen

### Schritt 10: Split Out + Merge für Datenbankspeigerung

**Problem:** SAP gibt alle Daten als ein Item zurück, Claude gibt 5 separate Items zurück → Merge schlägt fehl

**Lösung:** Split Out Node zwischen SAP und claude_code:
```
SAP → Split Out → claude_code → HTTP Claude → Merge (Input 1)
               → ────────────────────────── → Merge (Input 2)
```

`Split Out` Field: `d.results` → splittet Array in einzelne Items

**Merge Output:**
```
5 Items, jedes enthält:
✅ SAP Daten (AddressID, Email, Person)
✅ Claude Analyse (content[0].text)
✅ Risiko Level (VERDÄCHTIG/UNAUFFÄLLIG/PRÜFEN)
```

### Schritt 11: Supabase Integration

**Tabelle erstellt:**
```sql
CREATE TABLE fraud_detection_results (
  id BIGSERIAL PRIMARY KEY,
  address_id TEXT,
  email TEXT,
  person TEXT,
  claude_analyse TEXT,
  risiko_level TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Wichtige Entscheidung:** Supabase API statt direkter PostgreSQL Verbindung
- Grund: DB Passwort Reset würde bestehende Django SPV2 Verbindungen brechen
- Lösung: Supabase Node mit Service Key (kein Passwort nötig)

**Erste Einträge in der Datenbank:**
```json
{
  "id": 1,
  "address_id": "22820",
  "email": "info@10100001.com",
  "claude_analyse": "**VERDÄCHTIG**...",
  "risiko_level": "VERDÄCHTIG",
  "created_at": "2026-05-15 17:57:33"
}
```

---

## 🏗️ Finale Workflow Architektur

```
Manual Trigger
    ↓
HTTP Request (SAP OData API)
    ↓
Split Out (d.results → einzelne Items)
    ↓                    ↓
claude_code          (SAP Rohdaten)
    ↓                    ↓
HTTP Request         (für Merge)
(Claude Haiku)           ↓
    ↓                    ↓
    └──────── Merge ─────┘
                 ↓
         ┌───────┴───────┐
         ↓               ↓
    Supabase        Code JS1
    (Insert)    (Zusammenfassung)
                         ↓
                    Send Email
                    (GMX SMTP)
```

---

## 📚 Wichtigste Lernpunkte

### Security
```
❌ API Keys NIE direkt in Nodes eintragen
❌ API Keys NIE im Code hardcoden
✅ n8n Credentials verwenden (verschlüsselt)
✅ .env für lokale Entwicklung
✅ .gitignore schützt .env
```

### n8n Best Practices
```
✅ Separation of Concerns — ein Node, eine Aufgabe
✅ Code Nodes für Datentransformation
✅ Credentials für alle API Keys
✅ Workflow als JSON exportieren und in Git versionieren
✅ Mock Daten für Entwicklung wenn API down ist
```

### SAP OData
```
✅ Header muss exakt "APIKey" heißen (Groß-/Kleinschreibung!)
✅ Sandbox ist manchmal down (Vatertag, Wochenende)
✅ Daten kommen verschachtelt: d.results[n].Feldname
✅ Split Out Node nötig um Arrays aufzuteilen
```

### Claude API
```
✅ Modell-Namen exakt aus Dokumentation
✅ Body als Raw JSON mit JSON.stringify($json)
✅ anthropic-version Header immer mitschicken
✅ content[0].text für den Antworttext
```

### Node.js / Umgebung
```
✅ fnm für parallele Node Versionen
✅ Batch-Datei als elegante Lösung für Versions-Konflikt
✅ Node v22 LTS für n8n, v25 für andere Projekte
```

---

## 🚧 Noch offen

```
→ Workflow komplett end-to-end testen (Execute Workflow)
→ Teams Benachrichtigung (Azure App Registration nötig)
→ SAP zurückschreiben (CSRF Token Mechanismus)
→ Deployment auf Railway
→ Automatischer Trigger (statt Manual)
→ README.md vervollständigen
→ Finaler Git Commit mit komplettem Workflow
```

---

## 💡 Nächste Schritte

1. **Sofort:** Workflow Export + Git Commit
2. **Nächste Session:** Teams Node + Azure App Registration
3. **Danach:** Automatischer Trigger (Schedule oder Webhook)
4. **Langfristig:** Deployment auf Railway

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

*Dokumentiert am 15.05.2026 — SAP × n8n × Claude Fraud Detection Workflow*