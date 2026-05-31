"""
Email Verification — Test Layer 3 + 4
======================================
Testet Entropy Check (Layer 3) und Isolation Forest (Layer 4)
mit einem kleinen Testdatensatz ohne Flask und ohne n8n.

Output: Farbige Icons pro Spalte
    Erwartet:  ✅ normal  ❌ spam
    L3/L4:     🟢 ok  🟡 leicht verdächtig  🔴 stark verdächtig
    Ergebnis:  ✅ korrekt  ❌ falsch

Voraussetzung:
    → models/email_isolation_forest.pkl muss existieren
    → models/email_feature_cols.pkl muss existieren
    → data/test_emails.json muss existieren

Starten:
    cd C:\\Users\\tsinn\\VSCode\\Repos\\sap_n8n_demo
    venv_sap\\Scripts\\activate
    python python/training/test_layer34.py
"""

import json
import math
import joblib
import pandas as pd

# ============================================================
# 1. FARBEN + ICONS
# ============================================================

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"

def color(text, code):
    return f"{code}{text}{RESET}"

def l3_icon(entropy_status):
    if entropy_status == 'OK':       return '🟢'
    if entropy_status == 'SLIGHT':   return '🟡'
    if entropy_status == 'SUSPICIOUS': return '🔴'
    return '⚪'

def l4_icon(score):
    if score >= 0.0:    return '🟢'
    if score >= -0.05:  return '🟡'
    return '🔴'

def expected_icon(expected):
    return '✅' if expected == 'normal' else '❌'

def result_icon(correct):
    return '✅' if correct else '❌'

# ============================================================
# 2. MODELL LADEN
# ============================================================

print("=" * 65)
print("EMAIL VERIFICATION — TEST LAYER 3 + 4")
print("=" * 65)

model       = joblib.load('models/email_isolation_forest.pkl')
feature_cols = joblib.load('models/email_feature_cols.pkl')
print(f"\n✅ Modell geladen\n")

# ============================================================
# 3. HILFSFUNKTIONEN
# ============================================================

def calc_entropy(text):
    if not text:
        return 0.0
    freq = {}
    for c in text:
        freq[c] = freq.get(c, 0) + 1
    n = len(text)
    return -sum((f/n) * math.log2(f/n) for f in freq.values())


def check_entropy(email):
    """
    Layer 3 — drei Stufen:
    🟢 OK:         1.0 <= entropy <= 3.5
    🟡 SLIGHT:     3.5 < entropy <= 3.8
    🔴 SUSPICIOUS: entropy > 3.8 oder < 1.0
    """
    if '@' not in email:
        return 'INVALID', 0.0, 0.0

    local  = email.split('@')[0]
    domain = email.split('@')[1].split('.')[0]

    local_e  = round(calc_entropy(local), 4)
    domain_e = round(calc_entropy(domain), 4)

    def grade(e):
        if e < 1.0 or e > 3.8:  return 'SUSPICIOUS'
        if e > 3.5:              return 'SLIGHT'
        return 'OK'

    local_grade  = grade(local_e)
    domain_grade = grade(domain_e)

    # schlechteste Note gewinnt
    for g in ['SUSPICIOUS', 'SLIGHT', 'OK']:
        if local_grade == g or domain_grade == g:
            return g, local_e, domain_e


SUSPICIOUS_TLDS  = {'biz','xyz','info','click','top','win','loan','work','online','site'}
TRUSTED_DOMAINS  = {'gmail','outlook','yahoo','web','gmx','hotmail','icloud','protonmail'}

def extract_features(email):
    if '@' not in email:
        return None
    local, domain_full = email.split('@', 1)
    domain_parts  = domain_full.split('.')
    domain_name   = domain_parts[0]
    tld           = domain_parts[-1] if len(domain_parts) > 1 else ''

    digit_count   = sum(c.isdigit() for c in local)
    digit_ratio   = round(digit_count / len(local), 4) if local else 0
    special_chars = sum(1 for c in local if not c.isalnum() and c not in '._')

    return {
        'local_entropy':     round(calc_entropy(local), 4),
        'domain_entropy':    round(calc_entropy(domain_name), 4),
        'digit_ratio':       digit_ratio,
        'special_chars':     special_chars,
        'local_length':      len(local),
        'domain_length':     len(domain_name),
        'is_trusted_domain': 1 if domain_name.lower() in TRUSTED_DOMAINS else 0,
        'is_suspicious_tld': 1 if tld.lower() in SUSPICIOUS_TLDS else 0,
        'has_dot':           1 if '.' in local else 0,
        'has_underscore':    1 if '_' in local else 0,
        'shortest_part':     min(len(p) for p in local.split('.')) if '.' in local else len(local),
        'longest_part':      max(len(p) for p in local.split('.')) if '.' in local else len(local),
    }

# ============================================================
# 4. TESTDATEN LADEN
# ============================================================

with open('data/test_emails.json', encoding='utf-8') as f:
    test_data = json.load(f)

print(f"📊 {len(test_data)} Emails  |  "
      f"Normal: {len([x for x in test_data if x['expected']=='normal'])}  |  "
      f"Spam: {len([x for x in test_data if x['expected']=='spam'])}\n")

# ============================================================
# 5. TEST AUSGABE
# ============================================================

header = f"{'Email':<48} {'Exp':>3}  {'L3':>2}  {'L4':>2}  {'OK?':>3}"
print(header)
print("-" * 65)

results = []

for entry in test_data:
    email    = entry['email']
    expected = entry['expected']

    # Layer 3
    e_status, local_e, domain_e = check_entropy(email)

    # Layer 4
    features = extract_features(email)
    if features:
        df_row     = pd.DataFrame([features])[feature_cols]
        prediction = model.predict(df_row)[0]
        score      = round(model.decision_function(df_row)[0], 4)
        iso_label  = 'spam' if prediction == -1 else 'normal'
    else:
        score     = 0.0
        iso_label = 'invalid'

    # Gesamturteil — Layer 4 entscheidet, Layer 3 nur bei SUSPICIOUS
    flagged = (e_status == 'SUSPICIOUS') or (iso_label == 'spam')
    verdict = 'spam' if flagged else 'normal'
    correct = verdict == expected

    # Icons
    exp_i    = expected_icon(expected)
    l3_i     = l3_icon(e_status)
    l4_i     = l4_icon(score)
    result_i = result_icon(correct)

    # Email einfärben
    email_col = color(f"{email:<48}", GREEN if verdict == 'normal' else RED)

    print(f"{email_col} {exp_i}   {l3_i}   {l4_i}   {result_i}")

    results.append({
        'expected': expected,
        'verdict':  verdict,
        'correct':  correct,
    })

# ============================================================
# 6. ZUSAMMENFASSUNG
# ============================================================

total          = len(results)
correct_count  = sum(1 for r in results if r['correct'])
spam_res       = [r for r in results if r['expected'] == 'spam']
normal_res     = [r for r in results if r['expected'] == 'normal']
spam_caught    = sum(1 for r in spam_res    if r['verdict'] == 'spam')
false_pos      = sum(1 for r in normal_res  if r['verdict'] == 'spam')

print("\n" + "=" * 65)
print(f"  Gesamt korrekt:   {color(f'{correct_count}/{total} ({int(correct_count/total*100)}%)', GREEN)}")
print(f"  Spam erkannt:     {color(f'{spam_caught}/{len(spam_res)}', GREEN)}")
print(f"  False Positives:  {color(str(false_pos), RED if false_pos > 0 else GREEN)}/{len(normal_res)}")
print("=" * 65)

print("\nLegende:  ✅ normal / korrekt   ❌ spam / falsch")
print("          🟢 ok   🟡 leicht verdächtig   🔴 stark verdächtig\n")