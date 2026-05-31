# 2026-05-31 — Email Verification Workflow Komplett

## Was heute gebaut wurde

```
✅ Layer 3 Entropy Check in predict_server.py
✅ Layer 4 Isolation Forest in predict_server.py
✅ Email Forest Training Script (echte Daten aus Generator)
✅ Visueller Test Layer 3+4 mit Icons (🟢 🟡 🔴)
✅ n8n Email Verification Workflow komplett
✅ Supabase email_checks Tabelle mit DSGVO Konzept
✅ Git committed
```

---

## n8n Workflow Struktur

```
Manual Trigger
    ↓
SAP API (A_AddressEmailAddress)
    ↓
Code Node (aufbereiten)
    ↓
Flask /verify (Layer 1-4)
    ↓
Code Node (results aufteilen)
    ↓
IF Node (needs_claude?)
    ↓                    ↓
TRUE                   FALSE
    ↓                    ↓
Claude (Layer 5)      Merge Node
    ↓                    ↑
Code Node (parsen) ───┘
    ↓
Code Node (hash + features)
    ↓
Supabase (email_checks)
```

---

## SAP Endpoint für Emails

```
URL: https://sandbox.api.sap.com/s4hanacloud/sap/opu/odata/sap/API_BUSINESS_PARTNER/A_AddressEmailAddress

Parameter:
$top → 10 (Demo)

Felder:
AddressID, Person, EmailAddress
```

---

## Flask /verify Response

```json
{
  "total_checked": 5,
  "needs_claude": 4,
  "results": [
    {
      "email": "info@10100001.com",
      "mx_status": "DOMAIN_NOT_FOUND",
      "smtp_status": "SKIPPED",
      "entropy_status": "SUSPICIOUS",
      "local_entropy": 2.0,
      "domain_entropy": 0.9544,
      "iso_status": "SUSPICIOUS",
      "iso_score": -0.0709,
      "needs_claude": true,
      "tld": "com"
    }
  ]
}
```

---

## Claude Prompt (Layer 5)

```
Du bist ein Email Fraud Detection Experte.

Analysiere diese Email-Adresse:
Email: {{ $json.email }}
Domain: {{ $json.domain }}
Entropy Status: {{ $json.entropy_status }}
ISO Score: {{ $json.iso_score }}
MX Status: {{ $json.mx_status }}

Antworte NUR mit JSON:
{"verdict": "spam" oder "normal", "reason": "kurze Begründung", "confidence": 0.0-1.0}
```

---

## Supabase Tabelle email_checks

```sql
email_hash      ← simpleHash der Email (Anonymisierung)
features        ← JSON {local_entropy, domain_entropy, iso_score...}
verdict         ← normal / spam
needs_claude    ← bool
claude_verdict  ← spam (0.95) oder null
source          ← sap_demo / registration / contact
mx_status       ← Layer 1 Ergebnis
smtp_status     ← Layer 2 Ergebnis
entropy_status  ← Layer 3 Ergebnis
iso_status      ← Layer 4 Ergebnis
iso_score       ← Layer 4 Score
consent         ← bool (DSGVO)
expires_at      ← created_at + 90 Tage
```

---

## Wichtige n8n Erkenntnisse

```
1. localhost → 127.0.0.1 verwenden (IPv4!)
   ECONNREFUSED ::1 = IPv6 Problem

2. Body für Flask:
   Content Type: Raw
   Raw Content Type: application/json
   Body: ={{ JSON.stringify($input.all().map(i => i.json)) }}

3. Claude braucht Header:
   anthropic-version: 2023-06-01

4. Model Name: claude-haiku-4-5-20251001

5. IF Node → zuerst results aufteilen mit Code Node!
   /verify gibt {total_checked, results} zurück
   → results.map() für einzelne Items

6. Merge Node → Position für gleiche Reihenfolge

7. crypto nicht verfügbar in n8n → simpleHash selbst bauen

8. Supabase Field Mapping direkt → kein Auto Map!
```

---

## DSGVO Konzept

```
Email wird NIE gespeichert!
→ simpleHash für Wiedererkennung (Whitelist)
→ Features für Retraining
→ Löschung nach 90 Tagen (expires_at)
→ consent = true Pflicht
```

---

## Ergebnis SAP Sandbox Emails

```
info@10100001.com        → spam (MX not found, numerische Domain)
alina.mueller@10100001.com → spam (Domain existiert nicht)
alexander.linke@10100001.com → spam (Domain existiert nicht)
info@10100002.com        → spam (ISO suspicious)
barbara.meger@10100002.com → normal (Layer 3+4 ok)
```

---

## Nächste Schritte

```
→ HIL Email Node (Layer 6) einbauen
→ Whitelist Check vor Layer 1
→ Workflow als JSON exportieren
→ RLS für kritische Supabase Tabellen
→ Claude Fallback wenn API down
```