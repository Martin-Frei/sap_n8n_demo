"""
SAP Sales Order — Flask Prediction Server

Dies ist ein lokaler REST API Server der Anomalie-Vorhersagen macht.
n8n schickt neue SAP Orders hierher → Flask antwortet mit Anomalien.

Flask Grundlagen:
- Flask ist wie Django, nur viel einfacher
- Django: viele Dateien (views.py, urls.py, settings.py, models.py...)
- Flask: EINE Datei, fertig
- Flask startet auf localhost:5001
- n8n (localhost:5678) ruft Flask per HTTP Request auf

Starten:
    cd C:\\Users\\tsinn\\VSCode\\Repos\\sap_n8n_demo
    venv_sap\\Scripts\\activate
    python python/predict/predict_server.py

Testen im Browser:
    http://localhost:5001/health

Testen mit PowerShell:
    Invoke-RestMethod -Uri http://localhost:5001/health
"""

from flask import Flask, jsonify, request
import joblib
import pandas as pd
import numpy as np
import os
import dns.resolver
import smtplib
import time
import random
import math

# ============================================================
# EMAIL VERIFICATION HELFER — Layer 3 + 4
# ============================================================

SUSPICIOUS_TLDS_EMAIL = {'biz','xyz','info','click','top','win','loan','work','online','site'}
TRUSTED_DOMAINS_EMAIL = {'gmail','outlook','yahoo','web','gmx','hotmail','icloud','protonmail','t-online'}

def calc_entropy(text):
    """Chaos-Messung: je höher, desto zufälliger der Text"""
    if not text:
        return 0.0
    freq = {}
    for c in text:
        freq[c] = freq.get(c, 0) + 1
    n = len(text)
    return -sum((f/n) * math.log2(f/n) for f in freq.values())

def check_entropy(email):
    """
    Layer 3 — Entropy Check mit drei Stufen:
    OK         → 1.0 <= entropy <= 3.5
    SLIGHT     → 3.5 < entropy <= 3.8
    SUSPICIOUS → entropy > 3.8 oder < 1.0
    """
    if '@' not in email:
        return 'INVALID', 0.0, 0.0
    local  = email.split('@')[0]
    domain = email.split('@')[1].split('.')[0]
    local_e  = round(calc_entropy(local), 4)
    domain_e = round(calc_entropy(domain), 4)
    def grade(e):
        if e < 1.0 or e > 3.8: return 'SUSPICIOUS'
        if e > 3.5:             return 'SLIGHT'
        return 'OK'
    for g in ['SUSPICIOUS', 'SLIGHT', 'OK']:
        if grade(local_e) == g or grade(domain_e) == g:
            return g, local_e, domain_e

def extract_email_features(email):
    """Layer 4 — Features für Email Isolation Forest"""
    if '@' not in email:
        return None
    local, domain_full = email.split('@', 1)
    domain_parts  = domain_full.split('.')
    domain_name   = domain_parts[0]
    tld           = domain_parts[-1] if len(domain_parts) > 1 else ''
    digit_count   = sum(c.isdigit() for c in local)
    digit_ratio   = round(digit_count / len(local), 4) if local else 0
    special_chars = sum(1 for c in local if not c.isalnum() and c not in '._')
    shortest_part = min(len(p) for p in local.split('.')) if '.' in local else len(local)
    longest_part  = max(len(p) for p in local.split('.')) if '.' in local else len(local)
    return {
        'local_entropy':     round(calc_entropy(local), 4),
        'domain_entropy':    round(calc_entropy(domain_name), 4),
        'digit_ratio':       digit_ratio,
        'special_chars':     special_chars,
        'local_length':      len(local),
        'domain_length':     len(domain_name),
        'is_trusted_domain': 1 if domain_name.lower() in TRUSTED_DOMAINS_EMAIL else 0,
        'is_suspicious_tld': 1 if tld.lower() in SUSPICIOUS_TLDS_EMAIL else 0,
        'has_dot':           1 if '.' in local else 0,
        'has_underscore':    1 if '_' in local else 0,
        'shortest_part':     shortest_part,
        'longest_part':      longest_part,
    }

# ============================================================
# 1. FLASK APP ERSTELLEN
# ============================================================

app = Flask(__name__)

# ============================================================
# 2. MODELLE LADEN — SAP + EMAIL
# ============================================================

# --- SAP Order Modell ---
MODEL_PATH = os.path.join('models', 'sap_isolation_forest.pkl')
ENCODER_CUSTOMER_PATH = os.path.join('models', 'label_encoder_customer.pkl')
ENCODER_USER_PATH = os.path.join('models', 'label_encoder_user.pkl')

print("🔄 Lade SAP Modell und Encoder...")
try:
    model = joblib.load(MODEL_PATH)
    le_customer = joblib.load(ENCODER_CUSTOMER_PATH)
    le_user = joblib.load(ENCODER_USER_PATH)
    print("✅ SAP Modell geladen!")
    print(f"   → Bekannte Kunden: {len(le_customer.classes_)}")
    print(f"   → Bekannte User:   {len(le_user.classes_)}")
except FileNotFoundError as e:
    print(f"❌ SAP Modell nicht gefunden: {e}")
    model = None

# --- Email Modell ---
EMAIL_MODEL_PATH    = os.path.join('models', 'email_isolation_forest.pkl')
EMAIL_FEATURES_PATH = os.path.join('models', 'email_feature_cols.pkl')

print("🔄 Lade Email Modell...")
try:
    email_model    = joblib.load(EMAIL_MODEL_PATH)
    email_features = joblib.load(EMAIL_FEATURES_PATH)
    print("✅ Email Modell geladen!")
except FileNotFoundError:
    print("⚠️  Email Modell nicht gefunden → Layer 4 deaktiviert")
    email_model    = None
    email_features = None

# ============================================================
# 3. ROUTEN
# ============================================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status":            "online",
        "sap_model_loaded":  model is not None,
        "email_model_loaded": email_model is not None,
        "known_customers":   len(le_customer.classes_) if model else 0,
        "known_users":       len(le_user.classes_) if model else 0
    })


@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({"error": "SAP Modell nicht geladen!"}), 500
    data = request.json
    if not data:
        return jsonify({"error": "Kein JSON Body gesendet"}), 400
    df = pd.DataFrame(data)
    print(f"\n📊 Neue Vorhersage: {len(df)} Orders empfangen")
    df['customer_encoded'] = df['customer_id'].apply(
        lambda x: le_customer.transform([x])[0] if x in le_customer.classes_ else -1
    )
    df['user_encoded'] = df['created_by'].apply(
        lambda x: le_user.transform([x])[0] if x in le_user.classes_ else -1
    )
    features = df[['net_amount', 'customer_encoded', 'user_encoded']]
    df['anomaly']       = model.predict(features)
    df['anomaly_score'] = model.decision_function(features)
    anomalies = df[df['anomaly'] == -1].copy()
    anomalies['risiko_level'] = anomalies['anomaly_score'].apply(
        lambda s: 'KRITISCH' if s < -0.1 else 'VERDÄCHTIG' if s < -0.05 else 'PRÜFEN'
    )
    print(f"   → Normal:    {len(df[df['anomaly'] == 1])}")
    print(f"   → Anomalien: {len(anomalies)}")
    result_columns    = ['sales_order','customer_id','net_amount','created_by','anomaly_score','risiko_level']
    available_columns = [c for c in result_columns if c in anomalies.columns]
    return jsonify({
        "total_orders":    len(df),
        "total_anomalies": len(anomalies),
        "anomalies":       anomalies[available_columns].to_dict(orient='records')
    })


@app.route('/retrain', methods=['POST'])
def retrain():
    global model, le_customer, le_user
    data = request.json
    if not data:
        return jsonify({"error": "Keine Trainingsdaten gesendet"}), 400
    df = pd.DataFrame(data)
    print(f"\n🔄 RETRAINING mit {len(df)} Orders...")
    le_customer = le_customer.fit(df['customer_id'])
    le_user     = le_user.fit(df['created_by'])
    df['customer_encoded'] = le_customer.transform(df['customer_id'])
    df['user_encoded']     = le_user.transform(df['created_by'])
    features = df[['net_amount', 'customer_encoded', 'user_encoded']]
    from sklearn.ensemble import IsolationForest
    model = IsolationForest(contamination=0.05, n_estimators=100, random_state=42)
    model.fit(features)
    joblib.dump(model,       MODEL_PATH)
    joblib.dump(le_customer, ENCODER_CUSTOMER_PATH)
    joblib.dump(le_user,     ENCODER_USER_PATH)
    print("✅ Retraining fertig!")
    return jsonify({
        "status":           "retrained",
        "training_rows":    len(df),
        "known_customers":  len(le_customer.classes_),
        "known_users":      len(le_user.classes_)
    })


@app.route('/verify', methods=['POST'])
def verify_email():
    """
    POST http://localhost:5001/verify

    5-Layer Email Verification:
    Layer 1: MX Check         → Domain hat Mailserver?
    Layer 2: SMTP Handshake   → Mailbox existiert?
    Layer 3: Entropy Check    → Struktur verdächtig?
    Layer 4: Isolation Forest → ML Anomalie Detection
    Layer 5: needs_claude Flag → geht zu Claude wenn 🟡 oder 🔴
    """
    data = request.json
    results = []

    for entry in data:
        email  = entry.get('EmailAddress', '')
        domain = email.split('@')[1] if '@' in email else ''

        # ── Layer 1 — MX Check ──────────────────────────────
        mx_status  = 'UNKNOWN'
        mx_records = None
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_status  = 'MX_FOUND'
        except dns.resolver.NXDOMAIN:
            mx_status = 'DOMAIN_NOT_FOUND'
        except dns.resolver.NoAnswer:
            mx_status = 'NO_MX_RECORD'
        except dns.resolver.Timeout:
            mx_status = 'TIMEOUT'
        except:
            mx_status = 'ERROR'

        # ── Layer 2 — SMTP Check ─────────────────────────────
        smtp_status = 'SKIPPED'
        if mx_status == 'MX_FOUND':
            try:
                mx_host = str(mx_records[0].exchange)
                server  = smtplib.SMTP(mx_host, 25, timeout=5)
                server.helo()
                server.mail('verify@check.local')
                code, msg   = server.rcpt(email)
                smtp_status = 'VALID' if code == 250 else f'SMTP_CODE_{code}'
                server.quit()
            except smtplib.SMTPConnectError:
                smtp_status = 'CONNECTION_REFUSED'
            except smtplib.SMTPServerDisconnected:
                smtp_status = 'SERVER_DISCONNECTED'
            except TimeoutError:
                smtp_status = 'TIMEOUT'
            except:
                smtp_status = 'ERROR'

        # ── Layer 3 — Entropy Check ──────────────────────────
        entropy_status, local_e, domain_e = check_entropy(email)

        # ── Layer 4 — Isolation Forest ───────────────────────
        iso_status = 'SKIPPED'
        iso_score  = None
        if email_model is not None:
            features = extract_email_features(email)
            if features:
                df_row     = pd.DataFrame([features])[email_features]
                prediction = email_model.predict(df_row)[0]
                iso_score  = round(float(email_model.decision_function(df_row)[0]), 4)
                iso_status = 'SUSPICIOUS' if prediction == -1 else 'OK'

        # ── Layer 5 Flag — geht zu Claude? ───────────────────
        # Regel: SLIGHT oder SUSPICIOUS bei L3 oder L4 → Claude prüft
        needs_claude = (
            entropy_status in ('SLIGHT', 'SUSPICIOUS') or
            iso_status == 'SUSPICIOUS' or
            (iso_score is not None and iso_score < 0.0)
        )

        results.append({
            'email':          email,
            'address_id':     entry.get('AddressID', ''),
            'person':         entry.get('Person', ''),
            'domain':         domain,
            'mx_status':      mx_status,
            'smtp_status':    smtp_status,
            'entropy_status': entropy_status,
            'local_entropy':  local_e,
            'domain_entropy': domain_e,
            'iso_status':     iso_status,
            'iso_score':      iso_score,
            'needs_claude':   needs_claude,
            'tld':            domain.split('.')[-1] if domain else '',
        })

        time.sleep(random.uniform(0.5, 2.0))

    total_needs_claude = sum(1 for r in results if r['needs_claude'])

    return jsonify({
        "total_checked": len(results),
        "needs_claude":  total_needs_claude,
        "results":       results
    })


# ============================================================
# 4. SERVER STARTEN
# ============================================================

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 SAP + Email — Prediction Server")
    print("=" * 60)
    print(f"📍 Server:  http://localhost:5001")
    print(f"📍 Health:  http://localhost:5001/health")
    print(f"📍 Predict: POST http://localhost:5001/predict")
    print(f"📍 Retrain: POST http://localhost:5001/retrain")
    print(f"📍 Verify:  POST http://localhost:5001/verify")
    print("=" * 60 + "\n")
    app.run(host='0.0.0.0', port=5001, debug=True)