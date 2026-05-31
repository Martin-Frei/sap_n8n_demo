"""
Email Verification — Isolation Forest Training
Layer 4: Anomalie Detection für Email Adressen

Ablauf:
1. CSV aus Generator laden
2. Isolation Forest trainieren
3. Modell speichern → models/email_isolation_forest.pkl

Starten:
    cd C:\\Users\\tsinn\\VSCode\\Repos\\sap_n8n_demo
    venv_sap\\Scripts\\activate
    python python/training/email_forest_train.py
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import os

# ============================================================
# 1. DATEN LADEN
# ============================================================

print("=" * 60)
print("EMAIL ISOLATION FOREST — TRAINING")
print("=" * 60)

df = pd.read_csv('python/generate/examples/sample_1000.csv')
print(f"\n📊 Trainingsdaten geladen: {len(df)} Emails")
print(f"   Normal: {len(df[df['label'] == 'normal'])}")
print(f"   Spam:   {len(df[df['label'] == 'spam'])}")

# ============================================================
# 2. ISOLATION FOREST TRAINIEREN
# ============================================================

feature_cols = [
    'local_entropy', 'domain_entropy', 'digit_ratio',
    'special_chars', 'local_length', 'domain_length',
    'is_trusted_domain', 'is_suspicious_tld', 'has_dot',
    'has_underscore', 'shortest_part', 'longest_part'
]

X = df[feature_cols]

print(f"\n🌲 Trainiere Isolation Forest...")
print(f"   Features: {feature_cols}")

model = IsolationForest(
    contamination=0.10,   # 10% Spam erwartet
    n_estimators=200,
    random_state=42
)

model.fit(X)
print("✅ Training fertig!")

# ============================================================
# 3. ERGEBNIS PRÜFEN
# ============================================================

df['prediction'] = model.predict(X)
df['score'] = model.decision_function(X)

anomalies = df[df['prediction'] == -1]
normal = df[df['prediction'] == 1]

print(f"\n📊 Ergebnis auf Trainingsdaten:")
print(f"   Normal erkannt:   {len(normal)}")
print(f"   Anomalie erkannt: {len(anomalies)}")

spam_caught = len(df[(df['label'] == 'spam') & (df['prediction'] == -1)])
print(f"\n🎯 Spam erkannt: {spam_caught}/100 ({spam_caught}%)")

print(f"\n🔴 Beispiel Anomalien:")
print(anomalies[['email', 'local_entropy', 'digit_ratio', 'score']].head(10).to_string(index=False))

# ============================================================
# 4. MODELL SPEICHERN
# ============================================================

os.makedirs('models', exist_ok=True)
joblib.dump(model, 'models/email_isolation_forest.pkl')
joblib.dump(feature_cols, 'models/email_feature_cols.pkl')

print(f"\n💾 Modell gespeichert: models/email_isolation_forest.pkl")
print(f"💾 Features gespeichert: models/email_feature_cols.pkl")

print("\n" + "=" * 60)
print("✅ EMAIL TRAINING FERTIG")
print("=" * 60)