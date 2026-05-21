

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

# ============================================================
# 1. FLASK APP ERSTELLEN
# ============================================================
# Das ist wie "django.setup()" — nur eine Zeile
# __name__ sagt Flask: "ich bin das Hauptprogramm"

app = Flask(__name__)

# ============================================================
# 2. MODELL + ENCODER LADEN
# ============================================================
# Beim Serverstart werden die gespeicherten Modelle geladen
# Das passiert NUR EINMAL — nicht bei jedem Request
# Deshalb ist predict() so schnell (Millisekunden)

MODEL_PATH = os.path.join('models', 'sap_isolation_forest.pkl')
ENCODER_CUSTOMER_PATH = os.path.join('models', 'label_encoder_customer.pkl')
ENCODER_USER_PATH = os.path.join('models', 'label_encoder_user.pkl')

print("🔄 Lade Modell und Encoder...")

try:
    model = joblib.load(MODEL_PATH)
    le_customer = joblib.load(ENCODER_CUSTOMER_PATH)
    le_user = joblib.load(ENCODER_USER_PATH)
    print("✅ Modell geladen!")
    print(f"   → {MODEL_PATH}")
    print(f"   → Bekannte Kunden: {len(le_customer.classes_)}")
    print(f"   → Bekannte User: {len(le_user.classes_)}")
except FileNotFoundError as e:
    print(f"❌ Modell nicht gefunden: {e}")
    print("   → Erst python/training/isolation_forest_train.py ausführen!")
    model = None

# ============================================================
# 3. ROUTEN DEFINIEREN (wie Django urls.py + views.py)
# ============================================================

# --- Health Check ---
# Einfacher Test ob der Server läuft
# Django Äquivalent: path('health/', health_view)

@app.route('/health', methods=['GET'])
def health():
    """
    GET http://localhost:5001/health
    
    Gibt zurück ob Server und Modell bereit sind.
    Wie ein Ping — "lebst du noch?"
    """
    return jsonify({
        "status": "online",
        "model_loaded": model is not None,
        "known_customers": len(le_customer.classes_) if model else 0,
        "known_users": len(le_user.classes_) if model else 0
    })


# --- Predict Route ---
# Hier passiert die eigentliche Arbeit

@app.route('/predict', methods=['POST'])
def predict():
    """
    POST http://localhost:5001/predict
    
    Erwartet JSON Body mit einer Liste von Orders:
    [
        {
            "sales_order": "2093",
            "customer_id": "USCU_S16",
            "net_amount": 425755.00,
            "created_by": "S4TESTER",
            "order_type": "OR",
            "creation_date": "2016-09-16"
        },
        ...
    ]
    
    Gibt zurück: nur die Anomalien mit Score
    """
    
    # Prüfen ob Modell geladen ist
    if model is None:
        return jsonify({
            "error": "Modell nicht geladen. Erst Training ausführen!"
        }), 500
    
    # JSON Body lesen
    # In Django: request.body oder request.data
    # In Flask:  request.json — einfacher!
    data = request.json
    
    if not data:
        return jsonify({"error": "Kein JSON Body gesendet"}), 400
    
    # In DataFrame umwandeln
    df = pd.DataFrame(data)
    
    print(f"\n📊 Neue Vorhersage: {len(df)} Orders empfangen")
    
    # --------------------------------------------------------
    # FEATURE ENGINEERING
    # --------------------------------------------------------
    # Kategorische Werte (Text) → Zahlen umwandeln
    # Isolation Forest kann nur mit Zahlen arbeiten
    
    # Problem: neue Kunden die das Modell nicht kennt
    # Lösung: unbekannte Kunden bekommen -1
    
    df['customer_encoded'] = df['customer_id'].apply(
        lambda x: le_customer.transform([x])[0] 
        if x in le_customer.classes_ 
        else -1  # unbekannter Kunde → sofort verdächtig!
    )
    
    df['user_encoded'] = df['created_by'].apply(
        lambda x: le_user.transform([x])[0] 
        if x in le_user.classes_ 
        else -1  # unbekannter User → verdächtig!
    )
    
    # Features zusammenstellen (gleiche wie beim Training!)
    features = df[['net_amount', 'customer_encoded', 'user_encoded']]
    
    # --------------------------------------------------------
    # VORHERSAGE
    # --------------------------------------------------------
    # predict():           1 = normal, -1 = Anomalie
    # decision_function(): je negativer, desto stärker die Anomalie
    
    df['anomaly'] = model.predict(features)
    df['anomaly_score'] = model.decision_function(features)
    
    # Nur Anomalien filtern
    anomalies = df[df['anomaly'] == -1].copy()
    
    # Risiko Level basierend auf Score
    anomalies['risiko_level'] = anomalies['anomaly_score'].apply(
        lambda score: 'KRITISCH' if score < -0.1 
        else 'VERDÄCHTIG' if score < -0.05 
        else 'PRÜFEN'
    )
    
    print(f"   → Normal: {len(df[df['anomaly'] == 1])}")
    print(f"   → Anomalien: {len(anomalies)}")
    
    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------
    # Nur die relevanten Spalten zurückgeben
    # n8n bekommt das als JSON Array
    
    result_columns = [
        'sales_order', 'customer_id', 'net_amount', 
        'created_by', 'anomaly_score', 'risiko_level'
    ]
    
    # Nur Spalten nehmen die existieren
    available_columns = [c for c in result_columns if c in anomalies.columns]
    
    result = anomalies[available_columns].to_dict(orient='records')
    
    return jsonify({
        "total_orders": len(df),
        "total_anomalies": len(anomalies),
        "anomalies": result
    })


# --- Retrain Route ---
# Für Workflow B: wöchentliches Retraining

@app.route('/retrain', methods=['POST'])
def retrain():
    """
    POST http://localhost:5001/retrain
    
    Trainiert das Modell mit neuen Daten neu.
    Wird von n8n Workflow B (wöchentlich) aufgerufen.
    
    Erwartet JSON Body mit allen historischen Orders.
    """
    global model, le_customer, le_user
    
    data = request.json
    
    if not data:
        return jsonify({"error": "Keine Trainingsdaten gesendet"}), 400
    
    df = pd.DataFrame(data)
    
    print(f"\n🔄 RETRAINING mit {len(df)} Orders...")
    
    # Encoder neu trainieren
    le_customer = le_customer.fit(df['customer_id'])
    le_user = le_user.fit(df['created_by'])
    
    df['customer_encoded'] = le_customer.transform(df['customer_id'])
    df['user_encoded'] = le_user.transform(df['created_by'])
    
    features = df[['net_amount', 'customer_encoded', 'user_encoded']]
    
    # Modell neu trainieren
    from sklearn.ensemble import IsolationForest
    model = IsolationForest(
        contamination=0.05,
        n_estimators=100,
        random_state=42
    )
    model.fit(features)
    
    # Speichern
    joblib.dump(model, MODEL_PATH)
    joblib.dump(le_customer, ENCODER_CUSTOMER_PATH)
    joblib.dump(le_user, ENCODER_USER_PATH)
    
    print("✅ Retraining fertig! Modell gespeichert.")
    
    return jsonify({
        "status": "retrained",
        "training_rows": len(df),
        "known_customers": len(le_customer.classes_),
        "known_users": len(le_user.classes_)
    })


# ============================================================
# 4. SERVER STARTEN
# ============================================================
# Das ist wie "python manage.py runserver" in Django
#
# host='0.0.0.0' → erreichbar von überall (nicht nur localhost)
# port=5001      → nicht 5000 (oft belegt), nicht 5678 (n8n)
# debug=True     → zeigt Fehler im Browser, auto-reload bei Änderungen
#                  In Produktion: debug=False!

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 SAP Anomalie Detection — Prediction Server")
    print("=" * 60)
    print(f"📍 Server: http://localhost:5001")
    print(f"📍 Health:  http://localhost:5001/health")
    print(f"📍 Predict: POST http://localhost:5001/predict")
    print(f"📍 Retrain: POST http://localhost:5001/retrain")
    print("=" * 60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )