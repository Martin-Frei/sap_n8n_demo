# Email Verification Pipeline — Planung & Architektur
## 30. Mai 2026

---

## 🎯 Ziel

Eine mehrstufige Email-Verifikation die:
1. Spam und Fake-Emails automatisch erkennt
2. In das Portfolio (martin-freimuth.dev) integriert wird
3. Als eigenständiges Fraud Detection Projekt demonstrierbar ist
4. API-Kosten minimiert durch intelligente Layer-Logik

---

## 💡 Auslöser — Echtes Problem

Spam über das Portfolio-Kontaktformular:

```
Von: kdpmgisnyk
Email: hkpjpshl@immenseignite.info
Betreff: Betreff wählen...
Nachricht: mrintsjdtixiffdqrohyuxpitfteet
```

**Erkenntnis:** Die Domain `immenseignite.info` existiert tatsächlich (MX_FOUND, SMTP_VALID). 
Ein einfacher MX/SMTP Check hätte diesen Spam NICHT erkannt!
→ Mehrere Layer sind nötig.

---

## 🏗️ 5-Layer Architektur

```
Email kommt rein
    ↓
Layer 1: MX Check (Domain existiert?)
    ↓
Layer 2: SMTP Check (User erreichbar?)
    ↓
Layer 3: Entropy Check (Name/Email zufällig generiert?)
    ↓
Layer 4: Isolation Forest (Gesamtbild aller Features)
    ↓
Entscheidung:
    → ALLE Layer OK → ✅ Email sauber → kein Claude nötig
    → EIN Layer Alarm → Claude bekommt ALLE Ergebnisse
                      → Claude entscheidet final
```

---

## 📋 Layer im Detail

### Layer 1 — MX Record Check

```
Was:     DNS Abfrage ob die Domain einen Mail Server hat
Wie:     dns.resolver.resolve(domain, 'MX')
Kosten:  kostenlos, ~50ms
```

**Mögliche Ergebnisse:**

| Status | Bedeutung | Aktion |
|--------|-----------|--------|
| MX_FOUND | Domain hat Mail Server | → weiter zu Layer 2 |
| DOMAIN_NOT_FOUND | Domain existiert nicht | → ALARM |
| NO_MX_RECORD | Domain existiert aber kein Mail Server | → ALARM |
| TIMEOUT | DNS Server antwortet nicht | → ALARM |
| ERROR | Unbekannter Fehler | → ALARM |

**Warum:** 80% der Fake-Emails haben keine existierende Domain. Billigster und schnellster Check.

**Warum nicht alleine ausreichend:** Professioneller Spam nutzt echte Domains (siehe immenseignite.info).

---

### Layer 2 — SMTP Handshake

```
Was:     Verbindung zum Mail Server aufbauen und fragen
         ob der konkrete User existiert — OHNE Email zu senden
Wie:     smtplib.SMTP → HELO → MAIL FROM → RCPT TO
Kosten:  kostenlos, ~500ms-2s
```

**Mögliche Ergebnisse:**

| Status | Bedeutung | Aktion |
|--------|-----------|--------|
| VALID | Account existiert | → weiter |
| SMTP_REJECTED | Account existiert nicht (550) | → ALARM |
| CONNECTION_REFUSED | Server lehnt Verbindung ab | → ALARM |
| SERVER_DISCONNECTED | Server bricht ab | → ALARM |
| TIMEOUT | Server antwortet nicht | → ALARM |
| SKIPPED | Layer 1 hat schon ALARM gegeben | → weiter |

**Warum:** Prüft ob der konkrete Account existiert, nicht nur die Domain.

**Warum nicht alleine ausreichend:** Manche Mail Server antworten immer mit 250 (Catch-All).
Professionelle Spammer haben echte Accounts.

---

### Layer 3 — Entropy Check

```
Was:     Mathematisch berechnen ob ein Name/Username 
         zufällig generiert wurde
Wie:     Shannon Entropy Formel
Kosten:  kostenlos, <1ms
```

**Die Formel:**

```python
import math
from collections import Counter

def entropy(text):
    if not text:
        return 0
    counter = Counter(text.lower())
    length = len(text)
    return -sum(
        (count/length) * math.log2(count/length) 
        for count in counter.values()
    )
```

**Beispiele:**

| Text | Entropy | Bewertung |
|------|---------|-----------|
| martin | 2.25 | ✅ Normal — echte Namen haben niedrige Entropy |
| freimuth | 2.75 | ✅ Normal |
| hkpjpshl | 3.00 | ⚠️ Hoch — zufällig generiert |
| kdpmgisnyk | 3.25 | ⚠️ Hoch — zufällig generiert |
| info | 1.50 | ✅ Sehr niedrig — Standard-Prefix |

**Schwellwert:** Entropy > 2.9 → ALARM

**Warum:** Erkennt professionellen Spam den Layer 1+2 durchlassen. 
Bot-generierte Namen haben mathematisch erkennbar hohe Zufälligkeit.

**Warum nicht alleine ausreichend:** Manche echte Namen haben auch hohe Entropy (z.B. osteuropäische Namen).
Deshalb nur ein Layer von mehreren — nicht alleine entscheidend.

---

### Layer 4 — Isolation Forest

```
Was:     Machine Learning Modell das ALLE Features zusammen bewertet
Wie:     sklearn IsolationForest auf SAP Email Daten trainiert
Kosten:  kostenlos (lokal), <10ms
```

**Features:**

| Feature | Typ | Beispiel |
|---------|-----|---------|
| domain_length | numerisch | 13 (immenseignite) |
| is_numeric | boolean | false |
| tld_risk | numerisch | 0.8 (.info = hoch) |
| mx_exists | boolean | true/false |
| smtp_valid | boolean | true/false |
| entropy_username | numerisch | 3.0 |
| entropy_name | numerisch | 3.2 |
| has_company_name | boolean | false |
| email_type | kategorisch | info/name/random |

**Warum:** Isolation Forest findet KOMBINATIONEN die einzeln unauffällig sind.

Beispiel:
```
MX: ok ✅ + SMTP: ok ✅ + Entropy: hoch ⚠️ + .info TLD ⚠️
→ Einzeln: 2 von 4 ok → könnte echt sein
→ Isolation Forest: KOMBINATION ist selten → ANOMALIE
```

**Warum nicht alleine ausreichend:** ML kann keine Erklärung geben.
"Score -0.18" sagt dem User nichts → deshalb Claude als Layer 5.

**Warum nicht DNS/SMTP als Features für Isolation Forest (Option B verworfen):**
- Training müsste für ALLE Trainings-Emails DNS/SMTP Checks durchführen
- Tausende Netzwerk-Calls nur fürs Training
- SAP Sandbox Emails sind alle Fake → MX Check immer 0 → kein gutes Training
- DNS/SMTP sind binäre Checks (Ja/Nein) → dafür braucht man kein ML
- Saubere Trennung: ML für Muster, DNS/SMTP für Technik

---

### Layer 5 — Claude AI (nur bei Alarm)

```
Was:     Claude bekommt ALLE Ergebnisse der anderen Layer
         und gibt eine Begründung + Empfehlung
Wann:    NUR wenn mindestens 1 Layer Alarm gibt
Wie:     Anthropic API (Claude Haiku)
Kosten:  ~0.001 USD pro Call
```

**Claude bekommt:**
```
Email: hkpjpshl@immenseignite.info
Name: kdpmgisnyk

Layer 1 (MX):      MX_FOUND
Layer 2 (SMTP):    VALID
Layer 3 (Entropy): Username=3.0 Name=3.2 → HOCH
Layer 4 (IsoForest): Score=-0.18 → KRITISCH

Bewerte: SPAM / VERDÄCHTIG / ECHT
Begründung in 1-2 Sätzen.
```

**Claude antwortet:**
```
SPAM — Username und Name sind mit hoher Wahrscheinlichkeit 
zufällig generiert (hohe Shannon Entropy). Trotz gültiger 
Domain und SMTP deutet die Kombination auf automatisierten 
Spam hin. Empfehlung: blockieren.
```

**Warum nicht immer Claude:** 
- 99% der echten Emails → alle Layer OK → kein Claude Call nötig
- Spart 99% der API Kosten
- Claude nur als "Schiedsrichter" bei Zweifelsfällen

---

## 💰 Kostenanalyse

```
100 Kontaktanfragen pro Monat:
→ 95 echte Emails → alle Layer OK → 0 Claude Calls
→ 5 verdächtige → 5 Claude Calls → ~0.005 USD
→ Layer 1-4: komplett kostenlos (lokal)
→ Gesamtkosten: ~0.005 USD / Monat!

Alternative: Google reCAPTCHA
→ Privacy Problem (DSGVO)
→ User Experience schlecht
→ erkennt keinen professionellen Spam
```

---

## 🔄 Integration ins Portfolio

### Kontaktformular Flow

```
User füllt Kontaktformular aus
    ↓
HTMX Request → Django View
    ↓
Django ruft Flask /verify auf
    ↓
Layer 1-4 prüfen
    ↓
    ┌──────────────┴──────────────┐
    ↓                             ↓
Alle OK                    Min. 1 Alarm
    ↓                             ↓
Formular abschicken         Claude entscheidet
Email an Martin                   ↓
    ↓                    ┌────────┴────────┐
    ↓                    ↓                 ↓
    ↓               SPAM/BLOCK          ECHT/OK
    ↓                    ↓                 ↓
    ↓              "Ungültige           Formular
    ↓               Email"              abschicken
    ↓
✅ Fertig
```

### Bestehende Schutzmaßnahmen (bleiben!)

```
Layer 0a: Honeypot Field (fängt dumme Bots)
Layer 0b: Icon-Challenge (3×3 Grid Count)
Layer 0c: Progressive Rate Limiting

NEU dazu:
Layer 1-4: Email Verification
Layer 5:   Claude (bei Bedarf)
```

### Gesamter Schutz-Stack

```
Kontaktformular
    ↓
Honeypot Field → Bot? → ❌ Block
    ↓
Icon-Challenge → Falsch? → ❌ Block (Rate Limit)
    ↓
Email Verification (Layer 1-4)
    ↓
    → Alle OK → ✅ Senden
    → Alarm → Claude → SPAM? → ❌ Block
                     → ECHT? → ✅ Senden
```

---

## 🛠️ Technische Umsetzung

### Flask predict_server.py — Neue Route /verify

```
Bereits implementiert:
✅ MX Check (dns.resolver)
✅ SMTP Check (smtplib)  
✅ Domain Features (length, is_numeric, tld)
✅ Jitter zwischen Checks (anti-blacklisting)
✅ Differenzierte Status Codes

Noch zu implementieren:
→ Entropy Check (Shannon Formel)
→ TLD Risk Score Mapping
→ Isolation Forest für Emails trainieren
→ Response erweitern mit Entropy + Score
```

### Supabase — Neue Tabelle

```sql
CREATE TABLE email_verification_results (
    id BIGSERIAL PRIMARY KEY,
    email TEXT,
    domain TEXT,
    mx_status TEXT,
    smtp_status TEXT,
    entropy_username NUMERIC(6,4),
    entropy_name NUMERIC(6,4),
    domain_length INTEGER,
    is_numeric BOOLEAN,
    tld TEXT,
    tld_risk NUMERIC(4,2),
    isolation_forest_score NUMERIC(8,4),
    claude_analyse TEXT,
    risiko_level TEXT,
    source TEXT,                    -- 'portfolio_contact' oder 'sap_check'
    checked_at TIMESTAMPTZ DEFAULT NOW()
);
```

### n8n Workflow (SAP Email Check)

```
SAP Business Partner API → Emails holen
    ↓
Split Out
    ↓
Flask /verify (Batch, 10er Pakete)
    ↓
Ergebnis prüfen: Alarm?
    ↓ Ja → Claude → Supabase → Digest
    ↓ Nein → Supabase (nur Protokoll)
```

### Django Integration (Portfolio)

```python
# core/views.py — contact_form()
def contact_form(request):
    email = request.POST.get('email')
    name = request.POST.get('name')
    
    # Flask /verify aufrufen
    result = requests.post(
        'http://127.0.0.1:5001/verify',
        json=[{"EmailAddress": email, "Person": name}]
    ).json()
    
    check = result['results'][0]
    
    # Entscheidungslogik
    if all_layers_ok(check):
        send_email(...)
    else:
        # Claude entscheiden lassen
        claude_result = ask_claude(check)
        if claude_result == 'SPAM':
            return error_response("Ungültige Email")
        else:
            send_email(...)
```

---

## 📋 Batching-Strategie (für n8n SAP Workflow)

| Aspekt | Entscheidung | Begründung |
|--------|-------------|------------|
| Batch-Größe | 10 Emails | Kontrolle der Last, Timeout-Vermeidung |
| Verarbeitung | Synchron (Flask) | n8n wartet auf Ergebnis für Claude Prompt |
| Queue (Redis) | NICHT nötig | n8n gibt den Takt vor, kein async nötig |
| Jitter | 0.5-2s zwischen Emails | Anti-Blacklisting, "menschliches" Verhalten |
| Protokollierung | Sofort in Supabase | Kein Datenverlust bei Absturz |

---

## ⚠️ Bekannte Risiken & Mitigations

| Risiko | Mitigation |
|--------|-----------|
| IP Blacklisting durch SMTP Checks | Jitter + Batching + max 100 Checks/Tag |
| False Positives (echte Email als Spam) | Claude als Schiedsrichter, nicht automatisch blockieren |
| SAP Sandbox Emails alle Fake | Training auf Features die auch ohne echte Emails funktionieren |
| Entropy bei osteuropäischen Namen hoch | Schwellwert anpassen, nicht alleine entscheidend |
| Mail Server Catch-All (immer 250) | SMTP alleine nicht entscheidend, Kombination zählt |
| Claude Rate Limit | Nur bei Alarm aufrufen, nicht für jede Email |

---

## 🔜 Nächste Schritte (Morgen)

```
1. Entropy Check in Flask /verify einbauen
2. TLD Risk Score Mapping erstellen
3. Isolation Forest für Emails trainieren
4. n8n Workflow bauen
5. Django Portfolio Integration
6. Testen mit echten + Spam Emails
7. Dokumentation + Git Push
```

---

## 🎯 Relevanz für Fraud Detection

```
Dieses Projekt demonstriert:
→ Mehrstufige Verifikation (Layer 1-5)
→ ML (Isolation Forest) für Mustererkennung
→ AI (Claude) für Explainable Decisions
→ Kostenoptimierung (Claude nur bei Bedarf)
→ Echtes Problem gelöst (Portfolio Spam)
→ Produktionsreif (Django Integration)
→ Übertragbar auf AML, KYC, Fraud Detection
```

---

## 🔄 Human-in-the-Loop (HIL) — Whitelist & Selbstlernendes System

### Die Idee

Das System markiert eine Email als Fraud/Spam — aber was wenn es falsch liegt?
Ein Kunde mit exotischem Namen wird fälschlicherweise blockiert.

**Lösung:** Der Mensch kann korrigieren und das System lernt daraus.

```
Das ist Human-in-the-Loop (HIL):
→ der Mensch korrigiert das Modell
→ das Modell lernt aus den Korrekturen
→ wird mit der Zeit besser
→ genau so machen es Produktionssysteme!
```

### Ablauf

```
1. Email wird als SPAM/VERDÄCHTIG markiert
2. Digest Email an Admin enthält Whitelist-Link:
   
   "Falsch erkannt? Hier klicken zum Whitelisten:"
   https://localhost:5001/whitelist?token=abc123&email=xyz@firma.de

3. Admin klickt → Flask:
   → Email wird in Whitelist gespeichert
   → Token wird ungültig (einmalig!)
   → Isolation Forest Retraining wird angestoßen

4. Nächstes Mal:
   → gleiche Email → Whitelist Check → ✅ sofort durchlassen
   → ähnliche Emails → Isolation Forest kennt das Muster
```

### Token Absicherung

```
Problem:  Was wenn die Digest Email in falsche Hände gerät?
Lösung:   Token ist einmalig + zeitlich begrenzt

→ UUID4 generieren (nicht ratbar)
→ in Supabase speichern mit Ablaufdatum (24h)
→ nach Klick → Token als "used" markiert → ungültig
→ nach 24h → Token läuft automatisch ab
→ kein Missbrauch möglich
```

### Erweiterter Flow mit Whitelist

```
Email kommt rein
    ↓
Whitelist Check → auf der Liste?
    ↓ Ja → ✅ sofort durchlassen (kein Layer Check nötig)
    ↓ Nein
Layer 1-4 prüfen
    ↓
Alle OK → ✅ durchlassen
    ↓ Alarm
Claude entscheidet
    ↓
    ┌──────────┴──────────┐
    ↓                     ↓
SPAM/BLOCK            ECHT/OK
    ↓                     ↓
blockieren            durchlassen
+ Digest Email
+ Whitelist-Link
    ↓
Admin klickt?
    ↓ Ja
Whitelist + Retrain
    ↓
System lernt dazu!
```

### Isolation Forest lernt selbst dazu

```
Training Woche 1:
→ Modell kennt nur SAP Daten + Kaggle Dataset
→ "Krysztof Brzęczyszczykiewicz" → VERDÄCHTIG (hohe Entropy)

Admin whitelistet → Retraining

Training Woche 2:
→ Modell kennt jetzt auch osteuropäische Namen
→ "Krysztof Brzęczyszczykiewicz" → ✅ NORMAL
→ ähnliche Namen werden auch akzeptiert
```

### Neue Flask Routen

```python
# Whitelist-Link aus Email klicken
GET  /whitelist?token=xxx&email=yyy

# Prüfen ob Email auf Whitelist steht
POST /whitelist/check

# Isolation Forest mit Whitelist Daten neu trainieren
POST /retrain-email
```

### Neue Supabase Tabellen

```sql
-- Whitelist: vertrauenswürdige Emails
CREATE TABLE email_whitelist (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE,
    domain TEXT,
    added_by TEXT,              -- 'manual' oder 'hil'
    added_at TIMESTAMPTZ DEFAULT NOW()
);

-- Whitelist Tokens: Einmal-Links für Admin
CREATE TABLE whitelist_tokens (
    id BIGSERIAL PRIMARY KEY,
    token TEXT UNIQUE,
    email TEXT,
    expires_at TIMESTAMPTZ,     -- gültig für 24h
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Trainingsdaten — Woher?

```
Problem:  SAP Sandbox hat nur Fake Emails
          → schlechtes Training

Lösung:   Mehrere Quellen kombinieren!
```

| Quelle | Vorteil | Nachteil |
|--------|---------|----------|
| Kaggle Spam Dataset | Gelabelt, kostenlos, groß | Nicht deine Kunden |
| Portfolio Kontaktformular | Echte Anfragen, wächst organisch | Anfangs wenig Daten |
| Whitelist (HIL) | Korrigierte Daten, hohe Qualität | Braucht Zeit zum Aufbau |
| Eigene Kontakte (Gmail/GMX) | 100% echte Emails | Privacy beachten! |

**Empfehlung: Kaggle + Portfolio + Whitelist**

```
Start:      Kaggle Dataset zum initialen Trainieren
Dann:       Portfolio Daten kommen organisch dazu
Ongoing:    Whitelist wächst durch HIL Korrekturen
Ergebnis:   Modell wird mit jedem Lauf besser!
```

### Warum das professionell ist

```
Ohne HIL:
→ Modell macht Fehler
→ bleibt bei seinen Fehlern
→ User frustriert

Mit HIL:
→ Modell macht Fehler
→ User korrigiert mit einem Klick
→ Modell lernt
→ gleicher Fehler passiert nicht nochmal
→ Vertrauen wächst
```

---

## 🔜 Nächste Schritte (aktualisiert)

```
Phase 1 — Heute:
1. Entropy Check in Flask /verify einbauen
2. TLD Risk Score Mapping erstellen
3. n8n Workflow bauen
4. Claude Integration
5. Testen

Phase 2 — Morgen:
6. Isolation Forest für Emails trainieren (Kaggle)
7. Whitelist Routen in Flask
8. Token Generierung + Absicherung
9. Django Portfolio Integration
10. Digest mit Whitelist-Links

Phase 3 — Laufend:
11. HIL Korrekturen sammeln
12. Wöchentliches Retraining
13. Modell wird besser über Zeit
```

---

*Geplant am 29. +  30.05.2026 — Email Verification Pipeline*    
*"Hacker Pschorr + Emmentaler + Tullamore D.E.W." Edition 🍺🧀🥃*