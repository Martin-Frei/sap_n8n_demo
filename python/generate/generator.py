"""
Email Address Generator
=======================
Generiert synthetische Email-Adressen für ML Training.

- Kulturell diverse Namen (18 Kulturkreise)
- RFC 2606 konforme Domains (nie erreichbar, nie echt!)
- Realistische Spam-Muster
- Konfigurierbar via config.yaml

Starten:
    cd email-address-generator
    python generator.py

Output:
    examples/sample_1000.csv
"""

import math
import os
import random
import string

import pandas as pd
import yaml

# ============================================================
# 1. CONFIG LADEN
# ============================================================

with open('config.yaml', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Einstellungen auslesen
TOTAL = config['output']['total_count']
SPAM_RATIO = config['output']['spam_ratio']
OUTPUT_FILE = config['output']['output_file']
SEED = config['output']['seed']

SPAM_COUNT = int(TOTAL * SPAM_RATIO)
NORMAL_COUNT = TOTAL - SPAM_COUNT

random.seed(SEED)

print("=" * 60)
print("EMAIL ADDRESS GENERATOR")
print("=" * 60)
print(f"\n📊 Gesamt:  {TOTAL}")
print(f"   Normal: {NORMAL_COUNT} ({int((1-SPAM_RATIO)*100)}%)")
print(f"   Spam:   {SPAM_COUNT}  ({int(SPAM_RATIO*100)}%)")
print(f"   Seed:   {SEED}")

# ============================================================
# 2. NAMEN + DOMAINS AUS CONFIG
# ============================================================

# Alle Vornamen aus allen Kulturkreisen zusammenführen
ALL_FIRST_NAMES = []
for culture, names in config['first_names'].items():
    ALL_FIRST_NAMES.extend(names)

# Alle Nachnamen aus allen Kulturkreisen zusammenführen
ALL_LAST_NAMES = []
for culture, names in config['last_names'].items():
    ALL_LAST_NAMES.extend(names)

NORMAL_DOMAINS = config['domains']['normal']
SPAM_TLDS = config['domains']['spam_tlds']
SEPARATORS = config['format']['separators']
SUFFIX_PROB = config['format']['suffix_probability']
SUFFIX_MIN = config['format']['suffix_range']['min']
SUFFIX_MAX = config['format']['suffix_range']['max']

SPAM_LOCAL_MIN = config['spam']['local_length']['min']
SPAM_LOCAL_MAX = config['spam']['local_length']['max']
SPAM_DOMAIN_MIN = config['spam']['domain_length']['min']
SPAM_DOMAIN_MAX = config['spam']['domain_length']['max']

print(f"\n📋 Vornamen geladen:  {len(ALL_FIRST_NAMES)}")
print(f"   Nachnamen geladen: {len(ALL_LAST_NAMES)}")
print(f"   Normale Domains:   {len(NORMAL_DOMAINS)}")
print(f"   Spam TLDs:         {len(SPAM_TLDS)}")

# ============================================================
# 3. ENTROPY FUNKTION
# ============================================================

def calc_entropy(text):
    """Chaos-Messung: je höher, desto zufälliger der Text"""
    if not text:
        return 0.0
    freq = {}
    for c in text:
        freq[c] = freq.get(c, 0) + 1
    n = len(text)
    return -sum((f/n) * math.log2(f/n) for f in freq.values())

# ============================================================
# 4. GENERATOR FUNKTIONEN
# ============================================================

def generate_normal_local():
    """
    Normaler lokaler Teil — vorname.nachname oder vorname_nachname
    Beispiele: martin.mueller, nguyen_thanh, maria.garcia1985
    """
    first = random.choice(ALL_FIRST_NAMES).lower()
    last = random.choice(ALL_LAST_NAMES).lower()

    # Sonderzeichen entfernen (z.B. ndung'u → ndungu)
    first = ''.join(c for c in first if c.isalnum() or c in '._-')
    last = ''.join(c for c in last if c.isalnum() or c in '._-')

    sep = random.choice(SEPARATORS)
    local = f"{first}{sep}{last}"

    # Optional: Jahreszahl anhängen (martin.mueller1985)
    if random.random() < SUFFIX_PROB:
        year = random.randint(SUFFIX_MIN, SUFFIX_MAX)
        local += str(year)

    return local


def generate_spam_local():
    """
    Spam lokaler Teil — zufällig generiert, hohe Entropie
    5 verschiedene Patterns aus config
    """
    patterns = config['spam']['patterns']
    pattern = random.choice(patterns)
    length = random.randint(SPAM_LOCAL_MIN, SPAM_LOCAL_MAX)

    if pattern == 'random_chars':
        # xk7f2q9p — nur Kleinbuchstaben + Zahlen
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choices(chars, k=length))

    elif pattern == 'digits_heavy':
        # user123456789 — viele Zahlen
        chars = string.digits + string.ascii_lowercase[:5]
        return ''.join(random.choices(chars, k=length))

    elif pattern == 'mixed_chaos':
        # xK7f2Q9p — Groß + Klein + Zahlen
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=length))

    elif pattern == 'short_random':
        # xk7f — kurz und wirr
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choices(chars, k=random.randint(3, 6)))

    elif pattern == 'long_random':
        # xk7f2q9pmnbvcxz — lang und wirr
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choices(chars, k=random.randint(12, 18)))

    # Fallback
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))


def generate_spam_domain():
    """
    Spam Domain — zufälliger Name + verdächtige TLD
    Beispiel: xk9q2.biz, random123.xyz
    """
    length = random.randint(SPAM_DOMAIN_MIN, SPAM_DOMAIN_MAX)
    chars = string.ascii_lowercase + string.digits
    name = ''.join(random.choices(chars, k=length))
    tld = random.choice(SPAM_TLDS)
    return name + tld


def generate_normal_email():
    local = generate_normal_local()
    domain = random.choice(NORMAL_DOMAINS)
    return f"{local}@{domain}"


def generate_spam_email():
    """
    50% Spam mit echten Domains → testet Layer 2-8!
    50% Spam mit fake TLDs → Layer 1 fängt ab

    Beispiele:
    bkk4cij@gmail.com      → echte Domain, wirrer lokaler Teil
    xk7f2q9@gmx.de         → echte Domain, random chars
    123456abc@web.de        → echte Domain, viele Zahlen
    xk9q2.biz              → fake TLD, Layer 1 fängt ab
    """
    local = generate_spam_local()
    if random.random() < 0.5:
        # Echte Domain → testet Layer 2-8!
        domain = random.choice(NORMAL_DOMAINS)
    else:
        # Fake TLD → Layer 1 fängt ab
        domain = generate_spam_domain()
    return f"{local}@{domain}"


# ============================================================
# 5. FEATURES BERECHNEN
# ============================================================

SUSPICIOUS_TLDS = set(tld.strip('.') for tld in SPAM_TLDS)
TRUSTED_DOMAINS = {'example', 'test'}


def extract_features(email, label):
    """
    Features für Isolation Forest Training.
    Keine Namen — nur Struktur und Muster!
    """
    if '@' not in email:
        return None

    local, domain_full = email.split('@', 1)
    domain_parts = domain_full.split('.')
    domain_name = domain_parts[0]
    tld = domain_parts[-1] if len(domain_parts) > 1 else ''

    # Entropie
    local_entropy = round(calc_entropy(local), 4)
    domain_entropy = round(calc_entropy(domain_name), 4)

    # Zahlen
    digit_count = sum(c.isdigit() for c in local)
    digit_ratio = round(digit_count / len(local), 4) if local else 0

    # Sonderzeichen (außer . und _)
    special_chars = sum(1 for c in local if not c.isalnum() and c not in '._')

    # Längen
    local_length = len(local)
    domain_length = len(domain_name)

    # Vertrauenswürdige Domain?
    is_trusted = 1 if domain_name.lower() in TRUSTED_DOMAINS else 0

    # Verdächtige TLD?
    is_suspicious_tld = 1 if tld.lower() in SUSPICIOUS_TLDS else 0

    # Punkt im lokalen Teil (vorname.nachname = normal)
    has_dot = 1 if '.' in local else 0

    # Unterstrich im lokalen Teil
    has_underscore = 1 if '_' in local else 0

    # Kürzester Teil bei Punkt-Trennung
    # j.mueller → shortest=1, longest=7 → Initiale → normal!
    # a.b       → shortest=1, longest=1 → beide kurz → verdächtig
    if '.' in local:
        parts = local.split('.')
        shortest_part = min(len(p) for p in parts)
        longest_part  = max(len(p) for p in parts)
    else:
        shortest_part = local_length
        longest_part  = local_length

    return {
        'email': email,
        'label': label,
        'local_entropy': local_entropy,
        'domain_entropy': domain_entropy,
        'digit_ratio': digit_ratio,
        'special_chars': special_chars,
        'local_length': local_length,
        'domain_length': domain_length,
        'is_trusted_domain': is_trusted,
        'is_suspicious_tld': is_suspicious_tld,
        'has_dot': has_dot,
        'has_underscore': has_underscore,
        'shortest_part': shortest_part,
        'longest_part': longest_part,
    }


# ============================================================
# 6. EMAILS GENERIEREN
# ============================================================

print(f"\n🔄 Generiere Emails...")

rows = []

# Normale Emails
for _ in range(NORMAL_COUNT):
    email = generate_normal_email()
    features = extract_features(email, label='normal')
    if features:
        rows.append(features)

# Spam Emails
for _ in range(SPAM_COUNT):
    email = generate_spam_email()
    features = extract_features(email, label='spam')
    if features:
        rows.append(features)

# Mischen (damit nicht alle normalen zuerst kommen)
random.shuffle(rows)

df = pd.DataFrame(rows)

# ============================================================
# 7. SPEICHERN
# ============================================================

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
df.to_csv(OUTPUT_FILE, index=False)

print(f"💾 Gespeichert: {OUTPUT_FILE}")
print(f"   Rows: {len(df)}")

# ============================================================
# 8. KURZE STATISTIK
# ============================================================

print(f"\n📊 Statistik:")
print(f"   Normal: {len(df[df['label'] == 'normal'])}")
print(f"   Spam:   {len(df[df['label'] == 'spam'])}")

print(f"\n📈 Entropie Vergleich:")
normal_df = df[df['label'] == 'normal']
spam_df = df[df['label'] == 'spam']

print(f"   Normal local_entropy:  Ø {normal_df['local_entropy'].mean():.3f}")
print(f"   Spam   local_entropy:  Ø {spam_df['local_entropy'].mean():.3f}")
print(f"   Normal digit_ratio:    Ø {normal_df['digit_ratio'].mean():.3f}")
print(f"   Spam   digit_ratio:    Ø {spam_df['digit_ratio'].mean():.3f}")

print(f"\n🔴 Beispiel Spam:")
print(df[df['label'] == 'spam'][['email', 'local_entropy', 'digit_ratio']].head(5).to_string(index=False))

print(f"\n✅ Beispiel Normal:")
print(df[df['label'] == 'normal'][['email', 'local_entropy', 'digit_ratio']].head(5).to_string(index=False))

print("\n" + "=" * 60)
print("✅ GENERATOR FERTIG")
print("=" * 60)