# 2026-05-31 — Aufbau, Optimierung & Erkenntnisse Layer 3 + 4

## Übersicht

Heute wurde die Email Verification Pipeline um Layer 3 (Entropy Check) 
und Layer 4 (Isolation Forest) erweitert. Dazu wurde ein eigener 
synthetischer Email-Datensatz Generator entwickelt.

---

## Was heute gebaut wurde

```
✅ generator.py      — synthetischer Email Generator mit config.yaml
✅ config.yaml       — 18 Kulturkreise, 180 Vor- + Nachnamen, RFC 2606 Domains
✅ email_forest_train.py — Isolation Forest Training auf synthetischen Daten
✅ test_layer34.py   — visueller Test mit Icons (🟢 🟡 🔴)
✅ predict_server.py — Layer 3 + 4 in /verify Route eingebaut
```

---

## Die 5-Layer Architektur

```
Layer 1: MX Check          → Domain hat Mailserver? (DNS)
Layer 2: SMTP Handshake    → Mailbox existiert wirklich?
Layer 3: Entropy Check     → Struktur verdächtig? (Mathematik)
Layer 4: Isolation Forest  → ML Anomalie Detection
Layer 5: Claude            → Kontext + Erklärung (nur bei 🟡 oder 🔴)
```

### Regel für Layer 5 (Claude):
```
entropy_status in (SLIGHT, SUSPICIOUS)  → Claude prüft
iso_status == SUSPICIOUS                → Claude prüft
iso_score < 0.0                         → Claude prüft
beides 🟢                               → nur Layer 1+2 als Absicherung
```

---

## Entropie — Kernkonzept Layer 3

### Was ist Entropie?
Entropie misst den "Chaos-Grad" eines Textes.

```python
def calc_entropy(text):
    freq = {}
    for c in text:
        freq[c] = freq.get(c, 0) + 1
    n = len(text)
    return -sum((f/n) * math.log2(f/n) for f in freq.values())
```

### Wertebereiche:
```
< 1.0          → 🔴 SUSPICIOUS  (zu simpel:  aaaaaaa@...)
1.0 - 3.5      → 🟢 OK          (normal:     martin.mueller@...)
3.5 - 3.8      → 🟡 SLIGHT      (leicht hoch: thomas.wagner@...)
> 3.8          → 🔴 SUSPICIOUS  (zu chaotisch: xk7f2q9p@...)
```

### Wichtige Erkenntnis — Bias Problem:
```
❌ Entropie auf NAMEN anwenden → kultureller Bias!
   nguyen, kowalski, alejandro → alle "verdächtig" für deutschen Algorithmus

✅ Entropie auf STRUKTUR anwenden:
   Beide Seiten des @ separat prüfen
   Struktur bewerten, nicht Herkunft!
```

### Beide Extremwerte sind verdächtig:
```
aaaaaaa@gmail.com   → Entropie = 0.0 → zu simpel → Spam!
xk7f2q9p@biz.xyz   → Entropie = 3.9 → zu chaotisch → Spam!
```

---

## Synthetischer Email Generator

### Warum kein Kaggle Dataset?
Alle Kaggle Spam-Datasets analysieren **Email-Inhalt** (Text, Body).
Wir analysieren **Email-Adress-Struktur** — kein passendes Dataset vorhanden.

### Lösung: RFC 2606 konforme Domains
```
@example.com   → per RFC reserviert → nie erreichbar → nie echt!
@example.org
@example.net
@test.com
```

Garantie: Email-Adresse ist nie erreichbar — aber strukturell realistisch.

### 18 Kulturkreise im Generator:
```
Deutsch, Französisch, Italienisch, Spanisch, Portugiesisch
Osteuropäisch, Russisch
Asiatisch Ostasien, Asiatisch Südasien, Südostasiatisch
Afrikanisch Westafrika, Afrikanisch Ostafrika
Amerikanisch, Latino
Arabisch, Türkisch, Skandinavisch, Niederländisch
```

→ 180 Vornamen + 180 Nachnamen → kein kultureller Bias!

### Spam Patterns:
```
random_chars   → xk7f2q9p        (nur random Buchstaben + Zahlen)
digits_heavy   → user123456789   (viele Zahlen)
mixed_chaos    → xK7f2Q9p        (Groß + Klein + Zahlen)
short_random   → xk7f             (kurz und wirr)
long_random    → xk7f2q9pmnbvcxz (lang und wirr)
```

---

## Isolation Forest — Layer 4

### Features (12 Stück):
```python
feature_cols = [
    'local_entropy',      # Chaos im lokalen Teil
    'domain_entropy',     # Chaos in der Domain
    'digit_ratio',        # Anteil Zahlen im lokalen Teil
    'special_chars',      # Sonderzeichen (außer . und _)
    'local_length',       # Länge lokaler Teil
    'domain_length',      # Länge Domain
    'is_trusted_domain',  # gmail, outlook, gmx... = 1
    'is_suspicious_tld',  # .biz, .xyz, .click... = 1
    'has_dot',            # vorname.nachname = 1
    'has_underscore',     # vorname_nachname = 1
    'shortest_part',      # kürzester Teil bei Punkt-Trennung
    'longest_part',       # längster Teil bei Punkt-Trennung
]
```

### Warum shortest_part + longest_part?
```
j.mueller → shortest=1 (Initiale!), longest=7 → normal
a.b       → shortest=1, longest=1  → beide kurz → verdächtig

mueller.j → genau gleich wie j.mueller → kulturell egal!
```

### Trainingsdaten:
```
900 normale Emails (generiert mit 18 Kulturkreisen)
100 Spam Emails    (5 verschiedene Patterns)
Seed: 42           (reproduzierbar)
```

### Ergebnis Training:
```
Spam erkannt auf Trainingsdaten: 70/100 (70%)
```

---

## Test Layer 3 + 4 — Visueller Output

### Icon System:
```
Erwartet:  ✅ normal   ❌ spam
L3/L4:     🟢 ok   🟡 leicht verdächtig   🔴 stark verdächtig
Ergebnis:  ✅ korrekt  ❌ falsch
```

### Testergebnis (50 Emails, 45 normal, 5 spam):
```
Gesamt korrekt:   44/50 (88%)
Spam erkannt:     4/5
False Positives:  5/45
```

### Analyse der Fehler:

**Spam durchgekommen (1x):**
```
q9fj2kxmn8v@click99.click  🟢 🟢 → geht zu Claude
→ ABER: Layer 1 MX Check blockiert click99.click sofort!
→ kein echtes Problem in der Gesamtarchitektur
```

**False Positives (5x):**
```
j.mueller@gmx.de          🟢 🟡  → geht zu Claude (zu kurz für Modell)
ali.hassan@web.de         🟢 🟡  → geht zu Claude (kurzer Name)
info@example-company.de   🟢 🔴  → geht zu Claude (domain zu lang)
kontakt@musterfirma.de    🟢 🟡  → geht zu Claude
m.schmidt1985@web.de      🟡 🟡  → geht zu Claude
```
→ Alle False Positives gehen zu Claude → Claude erkennt sie als normal!

---

## Wichtigste Erkenntnisse

### 1. Defense in Depth
```
Kein einzelner Layer ist perfekt.
Zusammen sind sie stark — genau wie in echter AML Detection.
```

### 2. False Positives vs False Negatives
```
False Positive: echter Kunde blockiert → schlechte UX → schlimmer!
False Negative: Spam kommt durch → Claude fängt ihn → ok!

→ Lieber zu Claude schicken als echten Kunden blockieren
```

### 3. Kultureller Bias in ML
```
Trainiert auf deutschen Daten → Nguyen, Kowalski = verdächtig
Lösung: Struktur bewerten, nicht Namen!
→ digit_ratio, is_suspicious_tld, entropy sind kulturneutral
```

### 4. Synthetische Daten vs Kaggle
```
Für Email-Adress-Struktur: synthetisch ist besser!
Kaggle Datasets = Email-Inhalt (NLP) → falscher Ansatz
RFC 2606 Domains = garantiert nicht erreichbar → sicher
```

### 5. Entropie alleine reicht nicht
```
aaaaaaa → Entropie 0.0 → kein Chaos → ABER Spam!
→ Beide Extremwerte verdächtig
→ Entropie nur als Signal, nicht als Urteil
```

---

## Nächste Schritte

```
→ Layer 4 in n8n Workflow einbinden
→ Claude Prompt für Layer 5 optimieren
→ HIL Whitelist System aufbauen
→ Django Portfolio Integration
→ generator.py als eigenes GitHub Repo veröffentlichen
```

---

## Dateistruktur

```
sap_n8n_demo/
├── python/
│   ├── generate/
│   │   ├── generator.py          ← Email Generator
│   │   ├── config.yaml           ← Konfiguration
│   │   └── examples/
│   │       └── sample_1000.csv   ← Trainingsdaten
│   ├── training/
│   │   ├── email_forest_train.py ← Layer 4 Training
│   │   └── test_layer34.py       ← Visueller Test
│   └── predict/
│       └── predict_server.py     ← Flask Server (alle 5 Layer)
├── models/
│   ├── sap_isolation_forest.pkl
│   ├── email_isolation_forest.pkl ← NEU
│   └── email_feature_cols.pkl     ← NEU
└── data/
    └── test_emails.json           ← 50 Test Emails
```