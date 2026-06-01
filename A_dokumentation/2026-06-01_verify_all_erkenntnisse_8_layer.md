# 2026-06-01 — verify_all.py Test: Erkenntnisse & 8-Layer Architektur

## Testlauf

```
Script:    python/training/verify_all.py
Input:     python/generate/examples/sample_200_real_domain.csv
Output:    data/verify_results_20260601_0641.csv
Dauer:     ~60 Minuten (20 Batches × 3 Minuten)
Batch:     10 Emails alle 3 Minuten (Anti-Blacklisting)
```

---

## Gesamtergebnis

```
Gesamt:           200 Emails
Normal:           180
Spam:              20

Gesamt korrekt:   191/200 (95%)
Spam erkannt:      20/20  (100%) ← alle durch L1!
False Positives:    9/180  (5%)  ← zu Claude nach Fix!
False Negatives:    0/20   (0%)  ← kein Spam durchgekommen!
```

---

## Layer Statistik

| Layer | Alarme | davon Spam | davon Normal | Bewertung |
|-------|--------|-----------|--------------|-----------|
| L1 DOMAIN_NOT_FOUND | 19 | 19 | 0 | ✅ Perfekt! |
| L2 Alarm (bei L1 ok) | 165 | 1 | 164 | ⚠️ Zu aggressiv alleine! |
| L3 SLIGHT/SUSPICIOUS | 28 | 6 | 22 | 🎯 Gutes Signal |
| L4 SUSPICIOUS/score<0 | 25 | 16 | 9 | 🎯 Gutes Signal |
| L3 + L4 gemeinsam | 11 | - | - | 💪 Stark kombiniert |
| needs_claude aktuell | 42 | - | - | ✅ Richtige Menge |

---

## Entscheidungsbaum (neue Regel)

```
L1 🔴 DOMAIN_NOT_FOUND
→ direkt SPAM, kein Claude nötig!

L1 🟢 MX_FOUND + L2 🔴
→ Claude aufrufen! (GoDaddy Parking, echte Spam Domains)

L1 🟢 + L2 🟢/🟡 + L3/L4/L5 🟡 oder 🔴
→ Claude aufrufen!

L1 🟢 + alles 🟢
→ NORMAL, fertig!

Claude (L6) sagt SPAM:
→ L7 HIL Email an Admin
→ Admin: ✅ Whitelist oder ❌ Blacklist
```

---

## 8-Layer Architektur (Final)

| Layer | Name | Technologie | Training? | Entscheidung |
|-------|------|-------------|-----------|--------------|
| L1 | MX Check | DNS | Nein | Domain existiert? |
| L2 | SMTP Handshake | SMTP | Nein | Mailbox existiert? |
| L3 | Entropy Check | Mathematik | Nein | Chaos-Messung |
| L4 | Konsonanten + Vokale | Mathematik | Nein | Sprach-Muster |
| L5 | Isolation Forest | ML | Ja | Anomalie Detection |
| L6 | Claude AI | LLM API | Nein | Kontext + Erklärung |
| L7 | Human in the Loop | Email + Flask | Nein | Admin entscheidet |
| L8 | Retraining | scikit-learn | Ja | System lernt! |

---

## SMTP Erkenntnisse (L2)

```
SMTP 🟢 VALID (akzeptiert SMTP Check):
→ Gmail, Googlemail, Mailbox.org

SMTP 🔴 (blockt SMTP Check — aber NORMAL!):
→ Hotmail, iCloud, Protonmail
→ GMX, Web.de, T-Online, Freenet
→ Yahoo, Outlook, Posteo

SMTP 🔴 (wirklich verdächtig):
→ GoDaddy geparkte Domains (fgca.info!)
→ Spam Domains
→ Nicht-existierende Domains
```

**Regel:**
```
L2 🔴 alleine → ignorieren (164 False Positives!)
L1 🟢 + L2 🔴 → Claude! (sicher ist sicher)
```

---

## Konsonanten + Vokal Layer (L4 NEU)

### Warum?
```
bkk4cij2v2heif → L3 Entropy 🟢 VERSAGT!
xjGJXke1Mo     → L3 Entropy 🟢 VERSAGT!
4pdzp6lfewvz   → L3 Entropy 🟢 VERSAGT!

Aber:
bkk → 3 Konsonanten hintereinander → verdächtig!
pdzp → 4 Konsonanten → sehr verdächtig!
xjGJX → 5 Konsonanten → SUSPICIOUS!
```

### Implementierung:
```python
# Deutsche/englische Digraphen als ein Zeichen zählen
# sch, ch, th, ph sind normale Lautkombinationen!
text = local.lower()
text = text.replace('sch', 's').replace('ch', 'c')
text = text.replace('th', 't').replace('ph', 'f')

# Max aufeinanderfolgende Konsonanten
max_cons = 0
current = 0
for c in text:
    if c.isalpha() and c not in 'aeiouäöü':
        current += 1
        max_cons = max(max_cons, current)
    else:
        current = 0

# Vokal Ratio (auf Original)
vowels = sum(1 for c in local.lower() if c in 'aeiouäöü')
vowel_ratio = vowels / len(local) if local else 0

# Bewertung — Schwelle bei 4/5 wegen deutscher Namen!
if max_cons >= 5 or vowel_ratio < 0.15:  → 🔴 SUSPICIOUS
if max_cons >= 4 or vowel_ratio < 0.25:  → 🟡 SLIGHT
else:                                     → 🟢 OK
```

### Warum Schwelle 4/5 statt 3/4?
```
schmidt   → schm → nach Digraph-Erkennung: sm → 2 → 🟢 ✅
schweizer → schw → nach Digraph-Erkennung: sw → 2 → 🟢 ✅
hochhauser → chh → nach Digraph-Erkennung: ch → 2 → 🟢 ✅
bergmann  → rg, nn → max 2 → 🟢 ✅

bkk4cij   → bkk → 3 → 🟡 SLIGHT → Claude! ✅
xjGJXke   → xjGJX → 5 → 🔴 SUSPICIOUS → Claude! ✅
pdzp      → pdzp → 4 → 🟡 SLIGHT → Claude! ✅

Regel: lieber 2x zu viel als 1x zu wenig!
→ Claude korrigiert False Positives!
```

### Kulturell universell:
```
Jede menschliche Sprache hat Vokale!
→ Deutsch, Englisch, Vietnamesisch,
   Arabisch, Swahili, Japanisch...
→ alle echten Namen haben Vokale!
→ kein echter Name hat 4+ Konsonanten
   hintereinander ohne Vokal!

Ausnahme: Tschechisch "strč prst skrz krk" ("Steck den Finger durch den Hals")
→ aber kommt nie in Email-Adressen vor! 😄
```

---

## GoDaddy Parking Problem

```
fgca.info → MX Record existiert (GoDaddy Server!)
→ L1: 🟢 MX_FOUND ← FALSCH!
→ L2: 🔴 SMTP rejected
→ L3: 🟡 SLIGHT
→ System: normal ← FALSCH! Durchschlüpfer!

Fix:
L1 🟢 + L2 🔴 → Claude!
Claude sieht: "1n6kvpuc8d1wj → spam (0.99)" ✅

Zusätzlich:
L4 Konsonanten: kvp → 3 Konsonanten → 🟡 → Claude!
```

---

## False Positives Analyse

```
9 normale Emails als spam markiert:

minh.lewandowski@gmx.de      → L3🟡 + L4🔴 (langer Mix + GMX blockt SMTP)
anne.janssen@gmx.de          → L4🔴 (kurzer Name, Isolation Forest)
minjun.sokolov1982@yahoo.com → L3🟡 + L4🔴 (asiatisch + russisch + Jahreszahl)
zainab_van_den_berg@mailbox  → L4🟡 (langer niederländischer Name)
mehmet.li@web.de             → L4🟡 (sehr kurzer Nachname "li")
wojciech_coulibaly@freenet   → L3🟡 + L4🟡 (polnisch + westafrikanisch)
mwangi.de_vries@yahoo.de     → L3🟡 + L4🔴 (kenianisch + niederländisch)
anastasia_nilsson1997@web.de → L4🔴 (Jahreszahl + langer Name)
alejandra.kumar1986@web.de   → L3🟡 + L4🔴 (spanisch + indisch + Jahreszahl)
```

**Muster:**
```
1. Kulturell gemischte Namen → höhere Entropie
2. Jahreszahlen → digit_ratio erhöht → L4 reagiert
3. Kurze Nachnamen (li, ez) → Isolation Forest findet ungewöhnlich
→ alle würden von Claude korrekt als normal erkannt!
```

---

## Jahreszahl Fix (geplant)

```python
import re
# Jahreszahl am Ende ist normal!
has_year = bool(re.search(r'(19|20)\d{2}', local))
if has_year:
    # Jahreszahl aus digit_ratio rausrechnen
    year_digits = 4
    adjusted_digits = digit_count - year_digits
    digit_ratio = max(0, adjusted_digits / len(local))
```

---

## Generator Fix (geplant)

```
Aktuell:
Spam → immer fake TLD (.biz, .xyz...)
→ Layer 1 fängt alle ab
→ Layer 2-8 nie wirklich getestet für Spam!

Fix:
50% Spam → echte Domain (gmail, gmx...)
           wirrer lokaler Teil (bkk4cij@gmail.com)
50% Spam → fake TLD (wie bisher)

Dann:
→ Layer 1 fängt 50% ab
→ Layer 2-8 werden für restliche 50% getestet
→ ehrlichere Erkennungsrate
```

---

## Nächste Schritte (Priorität)

```
P0: L4 Konsonanten + Vokal Layer einbauen
    → predict_server.py + test_layer34.py

P0: needs_claude Regel updaten
    → L1 🟢 + L2 🔴 → Claude
    → L1 🔴 → direkt spam

P1: Generator Fix
    → 50% Spam mit echten Domains

P1: Neu trainieren + zweiter Test
    → ehrliche Erkennungsrate mit echten Spam Domains

P2: Jahreszahl Fix in Feature Extraction
P2: Flask /whitelist + /blacklist Routes
P2: hil_token in Supabase Update Node
P3: RLS für kritische Supabase Tabellen
```

---

## SMTP Provider Verhalten

```
Provider          SMTP Verhalten    Häufigkeit
gmail.com         SMTP_CODE_550     häufig
googlemail.com    SMTP_CODE_550     häufig
mailbox.org       SMTP_CODE_550     häufig
hotmail.com       SERVER_DISCONNECTED häufig
icloud.com        SMTP_CODE_550     häufig
protonmail.com    SERVER_DISCONNECTED häufig
gmx.de            CONNECTION_REFUSED häufig
web.de            CONNECTION_REFUSED häufig
t-online.de       CONNECTION_REFUSED häufig
freenet.de        SMTP_CODE_550     häufig
posteo.de         SERVER_DISCONNECTED häufig
yahoo.com/de      SERVER_DISCONNECTED häufig
outlook.com       SERVER_DISCONNECTED häufig
```

→ Alle großen Provider blocken SMTP Checks!
→ L2 🔴 bei diesen Providern = NORMAL!
→ Nur L2 🔴 bei unbekannten Domains = verdächtig!