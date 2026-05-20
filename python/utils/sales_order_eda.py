"""
SAP Sales Order — Explorative Datenanalyse (EDA)

Analysiert die rohen SAP Order Daten:
- Datensatzgröße und Struktur
- Datentypen
- Fehlende Werte
- Kategorische Verteilung
- Vorbereitung für Isolation Forest

Datei: data/sap_order_raw.csv
Output: Terminal Ausgabe + Statistiken
"""



import pandas as pd

# Datei laden
df = pd.read_csv('data/sap_order_raw.csv')

print("=" * 60)
print("SAP ORDER DATEN — EXPLORATIVE ANALYSE")
print("=" * 60)

# 1. Überblick
print(f"\n📊 Datensatz Größe: {df.shape[0]} Zeilen, {df.shape[1]} Spalten")
print(f"\nSpalten: {df.columns.tolist()}")
input("\n⏸️ Drücke Enter zum Weitermachen...")

# 2. Datentypen
print(f"\n🔍 Datentypen:")
print(df.dtypes)
input("\n⏸️ Drücke Enter zum Weitermachen...")

# 3. Erste Zeilen
print(f"\n📋 Erste 5 Zeilen:")
print(df.head())
input("\n⏸️ Drücke Enter zum Weitermachen...")

# 4. Nur numerische Spalten mit describe
print(f"\n💰 NUMERISCHE SPALTEN STATISTIKEN:")
print(df[['net_amount']].describe())
input("\n⏸️ Drücke Enter zum Weitermachen...")

# 5. Fehlende Werte
print(f"\n⚠️ Fehlende Werte:")
print(df.isnull().sum())
input("\n⏸️ Drücke Enter zum Weitermachen...")

# 6. Unique Werte (Klassen)
print(f"\n🏢 KATEGORISCHE SPALTEN (Klassen):")
print(f"Unique Customers: {df['customer_id'].nunique()}")
print(f"Unique Organizations: {df['organization'].nunique()}")
print(f"Unique Order Types: {df['order_type'].nunique()}")
print(f"Unique Users: {df['created_by'].nunique()}")
print(f"Unique Delivery Status: {df['delivery_status'].nunique()}")

print(f"\n📋 Delivery Status Verteilung:")
print(df['delivery_status'].value_counts())
input("\n⏸️ Drücke Enter zum Weitermachen...")

print(f"\n📋 Customers Verteilung:")
print(df['customer_id'].value_counts())

print("\n" + "=" * 60)