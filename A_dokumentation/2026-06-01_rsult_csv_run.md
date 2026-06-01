# 2026-06-01 — Ergebnisse CSV Testläufe

## Referenz Dateien

```
Test 1: data/verify_results_20260601_0641.csv
        → 200 Emails, Spam nur mit fake TLDs
        → Layer 3 Entropy + Layer 5 Isolation Forest
        → OHNE Layer 4 Konsonanten

Test 2: data/verify_results_20260601_1238.csv
        → 200 Emails, Spam 50% echte Domains
        → Layer 3 Entropy + Layer 4 Konsonanten + Layer 5 Isolation Forest
        → MIT Layer 4 Konsonanten (neu!)
```

---

## Gesamtergebnis Vergleich

| Metrik | Test 1 | Test 2 |
|--------|--------|--------|
| Gesamt Emails | 200 | 200 |
| Normal | 180 | 180 |
| Spam | 20 | 20 |
| **Gesamt korrekt** | **191/200 (95%)** | **187/200 (93%)** |
| **Spam erkannt** | **20/20 (100%)** | **18/20 (90%)** |
| **False Positives** | **9/180 (5%)** | **11/180 (6%)** |
| Durchschlüpfer | 1 (fgca.info) | 2 |
| needs_claude | 42 | 178 ⚠️ |

---

## Layer Statistik

| Layer | Test 1 | Test 2 |
|-------|--------|--------|
| L1 Alarm (DOMAIN_NOT_FOUND) | 19 | 8 |
| L3 Alarm (SLIGHT/SUSPICIOUS) | 28 | 25 |
| L4 Konsonanten (neu in T2) | — | 24 |
| L4/L5 Isolation Forest | 25 | 19 |
| needs_claude | 42 | 178 |

---

## Spam mit echter Domain (Test 2)

12 Spam Emails mit echten Domains (gmail, hotmail, icloud...):

```
✅ 7dc4b6e7c448e7@hotmail.com    L3:OK  L4:SUSPICIOUS L5:OK
✅ 1n6kvpuc8d1wj@t-online.de    L3:SLIGHT L4:SUSPICIOUS L5:OK
❌ pv60vaiy4va13u1@hotmail.com  L3:OK  L4:OK         L5:OK  ← Durchschlüpfer!
✅ xto@yahoo.com                 L3:OK  L4:OK         L5:SUSPICIOUS
✅ ggvnyruiwqy6qktc89@icloud.com L3:SUSPICIOUS L4:SUSPICIOUS L5:OK
✅ 3bba2190b051d4@t-online.de   L3:OK  L4:SUSPICIOUS L5:OK
❌ P1uRr6YICt@yahoo.de          L3:OK  L4:SLIGHT     L5:OK  ← Durchschlüpfer!
✅ 2v37pqk@outlook.com          L3:OK  L4:SUSPICIOUS L5:OK
✅ 9p38@icloud.com              L3:OK  L4:SUSPICIOUS L5:SUSPICIOUS
✅ wiy@t-online.de              L3:OK  L4:OK         L5:SUSPICIOUS
✅ 91zdfkblcmp@icloud.com       L3:OK  L4:SUSPICIOUS L5:OK
✅ sv55@hotmail.com             L3:OK  L4:SUSPICIOUS L5:SUSPICIOUS

Erkannt: 10/12 (83%) ohne L2!
Durchschlüpfer: 2/12 → nur L2 hätte geholfen
```

---

## Durchschlüpfer Analyse

**Test 1:**
```
1n6kvpuc8d1wj@fgca.info
→ GoDaddy geparkte Domain → L1 🟢 (MX existiert!)
→ L3 🟡 + L4 🟡 → needs_claude = false (alter Code)
→ Mit neuem Fix: needs_claude = true → Claude ✅
```

**Test 2:**
```
pv60vaiy4va13u1@hotmail.com
→ L3:OK L4:OK L5:OK → alle Layer versagen!
→ Nur L2 SERVER_DISCONNECTED als Signal
→ needs_claude = true (L2 Regel) → zu Claude ✅

P1uRr6YICt@yahoo.de
→ L4:SLIGHT → schwaches Signal
→ needs_claude = true (L4 SLIGHT Regel) → zu Claude
→ aber final_verdict = normal weil nur SLIGHT
→ Fix: SLIGHT reicht für spam Verdacht!
```

---

## needs_claude Problem

```
Test 1: needs_claude = 42/200  (21%) ← ok
Test 2: needs_claude = 178/200 (89%) ← zu viel! ⚠️

Ursache:
→ L2 Regel: L1 🟢 + L2 🔴 → Claude
→ 90% aller normalen Emails haben L2 🔴!
→ Gmail, GMX, Web, T-Online... alle blocken SMTP!
```

**Geplanter Fix:**
```python
# L2 nur relevant wenn lokaler Teil verdächtig
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
        iso_status == 'SUSPICIOUS' or
        (iso_score is not None and iso_score < 0.0)
    )
)
```

---

## False Positives

**Test 1 (9 Stück):**
```
minh.lewandowski@gmx.de        → L4 🔴 (kulturell gemischt)
anne.janssen@gmx.de            → L4 🔴 (kurzer Name)
minjun.sokolov1982@yahoo.com   → L3🟡 + L4🔴 (Jahreszahl)
zainab_van_den_berg@mailbox.org → L4🟡
mehmet.li@web.de               → L4🟡 (kurzer Nachname)
wojciech_coulibaly@freenet.de  → L3🟡 + L4🟡
mwangi.de_vries@yahoo.de       → L3🟡 + L4🔴
anastasia_nilsson1997@web.de   → L4🔴 (Jahreszahl)
alejandra.kumar1986@web.de     → L3🟡 + L4🔴 (Jahreszahl)
```

**Test 2 (11 Stück) — 2 neue:**
```
+ priyakowalczyk@posteo.de     → L5🔴 (polnisch, ungewöhnlich)
+ john_kowalczyk@web.de        → L3🟡 + L4🔴 (polnisch)
```

**Muster:**
```
→ Polnische Namen: kowalczyk, lewandowski, szymanski
  → viele Konsonanten → L4 schlägt an
→ Jahreszahlen → digit_ratio erhöht → L4/L5 reagiert
→ Kulturell gemischt → höhere Entropie → L3 reagiert
→ Alle zu Claude → Claude korrigiert korrekt!
```

---

## SMTP Provider Verhalten (aus beiden Tests)

```
🟢 SMTP akzeptiert (VALID):
   gmail.com, googlemail.com, mailbox.org

🔴 SMTP geblockt (normal!):
   hotmail.com    → SERVER_DISCONNECTED
   icloud.com     → SMTP_CODE_550
   protonmail.com → SERVER_DISCONNECTED
   gmx.de         → CONNECTION_REFUSED
   web.de         → CONNECTION_REFUSED
   t-online.de    → CONNECTION_REFUSED
   freenet.de     → SMTP_CODE_550
   posteo.de      → SERVER_DISCONNECTED
   yahoo.com/de   → SERVER_DISCONNECTED
   outlook.com    → SERVER_DISCONNECTED
```

---

## Erkenntnisse & Nächste Schritte

```
✅ Layer 4 Konsonanten funktioniert!
   → 8/10 echte Spam ohne L2 erkannt
   → L4 ist der wichtigste neue Layer

⚠️ needs_claude zu aggressiv (178/200)
   → L2 Regel überarbeiten
   → nur bei verdächtigem lokalen Teil

⚠️ 2 Durchschlüpfer mit echter Domain
   → pv60vaiy4va13u1 → zu lang, digit_ratio 0.4
   → P1uRr6YICt → Groß/Klein Mix → Layer 4 schwach

🎯 Nächste Schritte:
P0: needs_claude Regel fixen
P0: Layer 0 Wegwerf Domain Blacklist (Disify API)
P1: Jahreszahl Fix in Feature Extraction
P1: Retraining mit echten Daten
P2: Flask /whitelist + /blacklist Routes
P2: Zweiter Test mit fixed needs_claude
```

---

## Vergleich Erkennungsrate

```
Ohne Claude (nur L1-L5):
Test 1: 95% (leichte Daten — nur fake TLDs)
Test 2: 93% (harte Daten — 50% echte Domains)

Mit Claude (L6):
→ beide Durchschlüpfer würden erkannt!
→ geschätzte Erkennungsrate: ~99%

Mit Layer 0 Wegwerf Blacklist:
→ mailinator, temp-mail etc. sofort blockiert
→ für Portfolio Use Case wichtiger als Spam Bots!
```
