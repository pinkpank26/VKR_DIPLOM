CREATE SCHEMA IF NOT EXISTS mailing;

CREATE TABLE IF NOT EXISTS mailing.users (
  id              BIGSERIAL PRIMARY KEY,
  email           TEXT UNIQUE NOT NULL,
  password_hash   TEXT NOT NULL,
  role            TEXT NOT NULL DEFAULT 'marketer',
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mailing.contacts (
  id                 BIGSERIAL PRIMARY KEY,
  email              TEXT UNIQUE NOT NULL,
  full_name          TEXT,
  external_client_id TEXT,
  consent            BOOLEAN NOT NULL DEFAULT TRUE,
  created_at         TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mailing.unsubscribes (
  id          BIGSERIAL PRIMARY KEY,
  contact_id  BIGINT NOT NULL REFERENCES mailing.contacts(id),
  reason      TEXT,
  created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(contact_id)
);

CREATE TABLE IF NOT EXISTS mailing.templates (
  id          BIGSERIAL PRIMARY KEY,
  name        TEXT NOT NULL,
  subject     TEXT NOT NULL,
  body        TEXT NOT NULL,  -- можно HTML
  created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mailing.campaigns (
  id           BIGSERIAL PRIMARY KEY,
  name         TEXT NOT NULL,
  description  TEXT,
  template_id  BIGINT NOT NULL REFERENCES mailing.templates(id),
  created_by   BIGINT NOT NULL REFERENCES mailing.users(id),
  status       TEXT NOT NULL DEFAULT 'draft', -- draft, queued, sending, done, stopped
  scheduled_at TIMESTAMP,
  created_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mailing.messages (
  id           BIGSERIAL PRIMARY KEY,
  campaign_id  BIGINT NOT NULL REFERENCES mailing.campaigns(id),
  contact_id   BIGINT NOT NULL REFERENCES mailing.contacts(id),
  subject      TEXT NOT NULL,
  body         TEXT NOT NULL,
  status       TEXT NOT NULL DEFAULT 'queued', -- queued, sent, failed, skipped
  attempts     INT NOT NULL DEFAULT 0,
  last_error   TEXT,
  created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
  sent_at      TIMESTAMP,
  UNIQUE(campaign_id, contact_id)
);

CREATE TABLE IF NOT EXISTS mailing.send_log (
  id          BIGSERIAL PRIMARY KEY,
  message_id  BIGINT NOT NULL REFERENCES mailing.messages(id),
  status      TEXT NOT NULL, -- sent, failed, retry
  smtp_code   TEXT,
  smtp_reply  TEXT,
  created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_campaign ON mailing.messages(campaign_id);
CREATE INDEX IF NOT EXISTS idx_messages_contact ON mailing.messages(contact_id);
CREATE INDEX IF NOT EXISTS idx_send_log_message ON mailing.send_log(message_id);