"""
SAP Sales Order — Isolation Forest Training
Workflow B: Wöchentliches Retraining

Liest alle Daten aus Supabase
Trainiert Isolation Forest
Speichert Modell als joblib

python python/training/isolation_forest_train.py

"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# 1. Daten aus CSV laden (später aus Supabase)
df = pd.read_csv('data/sap_order_raw.csv')

print("=" * 60)
print("ISOLATION FOREST — TRAINING")
print("=" * 60)
print(f"\n📊 Trainingsdaten: {len(df)} Rows")

# 2. Features vorbereiten
le_customer = LabelEncoder()
le_user = LabelEncoder()

df['customer_encoded'] = le_customer.fit_transform(df['customer_id'])
df['user_encoded'] = le_user.fit_transform(df['created_by'])

features = df[['net_amount', 'customer_encoded', 'user_encoded']]

print(f"📋 Features: {features.columns.tolist()}")

# 3. Isolation Forest trainieren
model = IsolationForest(
    contamination=0.05,    # 5% Anomalien erwartet
    n_estimators=100,      # 100 Bäume
    random_state=42
)

model.fit(features)
print(f"\n✅ Modell trainiert!")

# 4. Vorhersagen auf Trainingsdaten
df['anomaly'] = model.predict(features)
df['anomaly_score'] = model.decision_function(features)

anomalies = df[df['anomaly'] == -1]
normal = df[df['anomaly'] == 1]

print(f"\n📊 Ergebnis:")
print(f"   Normal:   {len(normal)} Orders")
print(f"   Anomalie: {len(anomalies)} Orders")

print(f"\n🔴 TOP 10 ANOMALIEN:")
top_anomalies = anomalies.nsmallest(10, 'anomaly_score')
print(top_anomalies[['sales_order', 'customer_id', 'net_amount', 'anomaly_score']])

# 5. Modell + Encoder speichern
os.makedirs('models', exist_ok=True)
joblib.dump(model, 'models/sap_isolation_forest.pkl')
joblib.dump(le_customer, 'models/label_encoder_customer.pkl')
joblib.dump(le_user, 'models/label_encoder_user.pkl')

print(f"\n💾 Modell gespeichert: models/sap_isolation_forest.pkl")
print(f"💾 Encoder gespeichert: models/label_encoder_*.pkl")

print("\n" + "=" * 60)
print("✅ TRAINING FERTIG")
print("=" * 60)
