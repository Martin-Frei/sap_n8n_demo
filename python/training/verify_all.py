"""
Email Verification — Kompletter Test aller 8 Layer
===================================================
Liest CSV mit Email-Adressen und prüft jede Email
durch alle 8 Layer. Ergebnis wird in CSV gespeichert.

Batching: 10 Emails alle 3 Minuten → Anti-Blacklisting

Output CSV:
    email, label, L1, L2, L3_entropy, L4_consonant,
    L5_iso, needs_claude, L6_claude_verdict,
    L6_claude_reason, L6_confidence, final_verdict, correct

Starten:
    cd C:\\Users\\tsinn\\VSCode\\Repos\\sap_n8n_demo
    venv_sap\\Scripts\\activate
    python python/training/verify_all.py
"""

import requests
import pandas as pd
import time
import json
import os
from datetime import datetime

# ============================================================
# KONFIGURATION
# ============================================================

FLASK_URL     = "http://127.0.0.1:5001/verify"
CLAUDE_URL    = "https://api.anthropic.com/v1/messages"
CLAUDE_KEY    = os.getenv("ANTHROPIC_API_KEY", "")

INPUT_CSV     = "python/generate/examples/sample_200_real_domain.csv"
OUTPUT_CSV    = f"data/verify_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

BATCH_SIZE    = 10
WAIT_MINUTES  = 3

# ============================================================
# FARBEN + ICONS
# ============================================================

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"

def green(t):  return f"{GREEN}{t}{RESET}"
def yellow(t): return f"{YELLOW}{t}{RESET}"
def red(t):    return f"{RED}{t}{RESET}"

def l1_icon(status):
    if status == 'MX_FOUND':  return green("🟢")
    if status == 'SKIPPED':   return "⚪"
    return red("🔴")

def l2_icon(status):
    if status == 'VALID':     return green("🟢")
    if status == 'SKIPPED':   return "⚪"
    return red("🔴")

def l3_icon(status):
    if status == 'OK':        return green("🟢")
    if status == 'SLIGHT':    return yellow("🟡")
    return red("🔴")

def l4_icon(status):
    """Layer 4 — Konsonanten Check"""
    if status == 'OK':        return green("🟢")
    if status == 'SLIGHT':    return yellow("🟡")
    if status == 'UNKNOWN':   return "⚪"
    return red("🔴")

def l5_icon(score):
    """Layer 5 — Isolation Forest"""
    if score is None:         return "⚪"
    if score >= 0.0:          return green("🟢")
    if score >= -0.05:        return yellow("🟡")
    return red("🔴")

def l6_icon(verdict):
    """Layer 6 — Claude"""
    if verdict is None:       return "⚪"
    if verdict == 'normal':   return green("🟢")
    return red("🔴")

def email_icon(label):
    return green("✅") if label == 'normal' else red("❌")

# ============================================================
# CLAUDE CALL
# ============================================================

def ask_claude(email_data):
    """Layer 6 — Claude analysiert verdächtige Emails"""
    if not CLAUDE_KEY:
        return None, "Kein API Key", 0.0

    prompt = f"""Du bist ein Email Fraud Detection Experte.

Analysiere diese Email-Adresse und antworte NUR mit JSON:

Email: {email_data['email']}
MX Status: {email_data['mx_status']}
SMTP Status: {email_data['smtp_status']}
Entropy Status: {email_data['entropy_status']}
Local Entropy: {email_data['local_entropy']}
Domain Entropy: {email_data['domain_entropy']}
Konsonanten Status: {email_data.get('consonant_status', 'UNKNOWN')}
Max Konsonanten: {email_data.get('max_consonants', 0)}
Vokal Ratio: {email_data.get('vowel_ratio', 0)}
ISO Status: {email_data['iso_status']}
ISO Score: {email_data['iso_score']}

Antworte NUR mit diesem JSON (kein Markdown):
{{"verdict": "spam" oder "normal", "reason": "kurze Begründung auf Deutsch", "confidence": 0.0-1.0}}"""

    try:
        response = requests.post(
            CLAUDE_URL,
            headers={
                "x-api-key": CLAUDE_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        text = response.json()['content'][0]['text']
        clean = text.replace('```json', '').replace('```', '').strip()
        parsed = json.loads(clean)
        return parsed['verdict'], parsed['reason'], parsed['confidence']
    except Exception as e:
        return None, f"Fehler: {str(e)}", 0.0

# ============================================================
# HAUPTPROGRAMM
# ============================================================

print("=" * 75)
print("EMAIL VERIFICATION — ALLE 8 LAYER")
print("=" * 75)

# CSV laden
df = pd.read_csv(INPUT_CSV)
print(f"\n📊 Emails geladen: {len(df)}")
print(f"   Normal: {len(df[df['label']=='normal'])}")
print(f"   Spam:   {len(df[df['label']=='spam'])}")
print(f"\n⏱️  Batch: {BATCH_SIZE} Emails alle {WAIT_MINUTES} Minuten")
print(f"   Geschätzte Dauer: {len(df) // BATCH_SIZE * WAIT_MINUTES} Minuten\n")

results = []
total_batches = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE

# Header
print(f"{'Email':<42} {'Exp':>3}  {'L1':>2}  {'L2':>2}  {'L3':>2}  {'L4':>2}  {'L5':>2}  {'L6':>2}  Kommentar")
print("-" * 105)

# Batches verarbeiten
for batch_num in range(total_batches):
    start = batch_num * BATCH_SIZE
    end   = min(start + BATCH_SIZE, len(df))
    batch = df.iloc[start:end]

    print(f"\n📦 Batch {batch_num + 1}/{total_batches} ({start+1}-{end})")

    payload = [
        {"EmailAddress": row['email'], "AddressID": str(i), "Person": ""}
        for i, row in batch.iterrows()
    ]

    try:
        response = requests.post(FLASK_URL, json=payload, timeout=120)
        verify_results = response.json()['results']
    except Exception as e:
        print(f"❌ Flask Fehler: {e}")
        continue

    for idx, (_, row) in enumerate(batch.iterrows()):
        vr = verify_results[idx] if idx < len(verify_results) else {}

        email             = row['email']
        label             = row['label']
        mx_status         = vr.get('mx_status', 'ERROR')
        smtp_status       = vr.get('smtp_status', 'ERROR')
        entropy_status    = vr.get('entropy_status', 'ERROR')
        consonant_status  = vr.get('consonant_status', 'UNKNOWN')
        max_cons          = vr.get('max_consonants', 0)
        vowel_ratio       = vr.get('vowel_ratio', 0.0)
        iso_status        = vr.get('iso_status', 'ERROR')
        iso_score         = vr.get('iso_score')
        local_entropy     = vr.get('local_entropy', 0)
        domain_entropy    = vr.get('domain_entropy', 0)
        needs_claude      = vr.get('needs_claude', False)

        # Layer 6 — Claude
        claude_verdict    = None
        claude_reason     = None
        claude_confidence = None

        if needs_claude and CLAUDE_KEY:
            claude_verdict, claude_reason, claude_confidence = ask_claude(vr)
            time.sleep(0.5)

        # Final Verdict
        if claude_verdict:
            final_verdict = claude_verdict
        elif mx_status != 'MX_FOUND':
            final_verdict = 'spam'
        elif iso_status == 'SUSPICIOUS' or consonant_status == 'SUSPICIOUS':
            final_verdict = 'spam'
        elif entropy_status == 'SUSPICIOUS':
            final_verdict = 'spam'
        else:
            final_verdict = 'normal'

        # Terminal Output
        comment = claude_reason[:35] if claude_reason else ""
        print(
            f"{email:<42} "
            f"{email_icon(label)}  "
            f"{l1_icon(mx_status)}  "
            f"{l2_icon(smtp_status)}  "
            f"{l3_icon(entropy_status)}  "
            f"{l4_icon(consonant_status)}  "
            f"{l5_icon(iso_score)}  "
            f"{l6_icon(claude_verdict)}  "
            f"{comment}"
        )

        results.append({
            'email':             email,
            'label':             label,
            'L1_mx':             mx_status,
            'L2_smtp':           smtp_status,
            'L3_entropy':        entropy_status,
            'L3_local_entropy':  local_entropy,
            'L3_domain_entropy': domain_entropy,
            'L4_consonant':      consonant_status,
            'L4_max_cons':       max_cons,
            'L4_vowel_ratio':    vowel_ratio,
            'L5_iso_status':     iso_status,
            'L5_iso_score':      iso_score,
            'needs_claude':      needs_claude,
            'L6_verdict':        claude_verdict,
            'L6_reason':         claude_reason,
            'L6_confidence':     claude_confidence,
            'final_verdict':     final_verdict,
            'correct':           final_verdict == label,
        })

    # Zwischenspeichern
    os.makedirs('data', exist_ok=True)
    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print(f"   💾 Zwischenspeichert: {len(results)} Emails")

    if batch_num < total_batches - 1:
        print(f"\n   ⏳ Warte {WAIT_MINUTES} Minuten bis zum nächsten Batch...")
        for remaining in range(WAIT_MINUTES * 60, 0, -30):
            print(f"      {remaining}s verbleibend...")
            time.sleep(30)

# ============================================================
# ZUSAMMENFASSUNG
# ============================================================

result_df = pd.DataFrame(results)
total     = len(result_df)
correct   = result_df['correct'].sum()
spam_df   = result_df[result_df['label'] == 'spam']
normal_df = result_df[result_df['label'] == 'normal']

spam_caught = (spam_df['final_verdict'] == 'spam').sum()
false_pos   = (normal_df['final_verdict'] == 'spam').sum()

print(f"\n{'='*75}")
print(f"📊 GESAMTERGEBNIS:")
print(f"   Gesamt korrekt:   {correct}/{total} ({int(correct/total*100)}%)")
print(f"   Spam erkannt:     {spam_caught}/{len(spam_df)}")
print(f"   False Positives:  {false_pos}/{len(normal_df)}")
print(f"\n💾 Gespeichert: {OUTPUT_CSV}")
print(f"{'='*75}")

print("\nLegende:")
print("  Exp:    ✅ normal   ❌ spam")
print("  L1-L6:  🟢 ok   🟡 leicht verdächtig   🔴 spam/blockiert   ⚪ nicht geprüft")
print("  L1: MX Check  L2: SMTP  L3: Entropy  L4: Konsonanten  L5: IsoForest  L6: Claude")