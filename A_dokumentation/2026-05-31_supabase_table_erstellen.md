-- ============================================================
-- Email Checks — Supabase Migration
-- ============================================================
-- Zweck: Anonyme Speicherung von Email-Verifikationsergebnissen
-- DSGVO: Nur Hash + Features, keine echte Email-Adresse
-- Löschung: nach 90 Tagen (automatisch via Supabase Cron)
-- ============================================================

CREATE TABLE email_checks (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Anonymisierung
    email_hash      TEXT NOT NULL,          -- sha256 der Email
    
    -- Features für Retraining Layer 4
    features        JSONB NOT NULL,         -- {local_entropy, digit_ratio, ...}
    
    -- Ergebnis
    verdict         TEXT NOT NULL,          -- 'normal' | 'spam' | 'unknown'
    needs_claude    BOOLEAN DEFAULT FALSE,  -- wurde Layer 5 aufgerufen?
    claude_verdict  TEXT,                   -- Claude Ergebnis wenn aufgerufen
    
    -- Herkunft
    source          TEXT NOT NULL,          -- 'registration' | 'contact' | 'honeypot'
    
    -- Layer Ergebnisse (für Monitoring)
    mx_status       TEXT,                   -- MX_FOUND | DOMAIN_NOT_FOUND | ...
    smtp_status     TEXT,                   -- VALID | SMTP_REJECTED | ...
    entropy_status  TEXT,                   -- OK | SLIGHT | SUSPICIOUS
    iso_status      TEXT,                   -- OK | SUSPICIOUS
    iso_score       FLOAT,                  -- Isolation Forest Score

    -- DSGVO
    consent         BOOLEAN DEFAULT FALSE,  -- Datenschutz zugestimmt?
    consent_at      TIMESTAMPTZ,            -- wann zugestimmt?
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ DEFAULT NOW() + INTERVAL '90 days'
);

-- Index für schnellen Whitelist Check
CREATE INDEX idx_email_hash ON email_checks(email_hash);

-- Index für Retraining Abfragen
CREATE INDEX idx_verdict ON email_checks(verdict);
CREATE INDEX idx_source  ON email_checks(source);

-- ============================================================
-- Whitelist View — bekannte OK Emails
-- ============================================================
CREATE VIEW email_whitelist AS
SELECT DISTINCT email_hash
FROM email_checks
WHERE verdict = 'normal'
  AND consent = TRUE;

-- ============================================================
-- Blacklist View — bekannte Spam Emails  
-- ============================================================
CREATE VIEW email_blacklist AS
SELECT DISTINCT email_hash
FROM email_checks
WHERE verdict = 'spam';

-- ============================================================
-- Retraining View — Features für Layer 4
-- ============================================================
CREATE VIEW email_training_data AS
SELECT 
    features,
    verdict,
    source,
    created_at
FROM email_checks
WHERE consent = TRUE
  AND verdict IN ('normal', 'spam')
  AND expires_at > NOW();

-- ============================================================
-- Kommentar
-- ============================================================
COMMENT ON TABLE email_checks IS 
'Anonyme Email-Verifikationsergebnisse für ML Retraining.
 Echte Email-Adressen werden NIE gespeichert — nur SHA256 Hash.
 DSGVO konform: Löschung nach 90 Tagen via expires_at.';