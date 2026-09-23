-- À exécuter UNE FOIS sur le container supabase-db (Contabo).
-- N'affecte PAS voltify / sooma / syras / postgres system.

-- 1) Créer le rôle applicatif
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'merveille_app') THEN
    CREATE ROLE merveille_app LOGIN PASSWORD 'CHANGE_ME_STRONG_PASSWORD';
  END IF;
END
$$;

-- 2) Créer la base dédiée
SELECT 'CREATE DATABASE merveille OWNER merveille_app'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'merveille')\gexec

-- 3) Droits
GRANT ALL PRIVILEGES ON DATABASE merveille TO merveille_app;

\c merveille
GRANT ALL ON SCHEMA public TO merveille_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO merveille_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO merveille_app;
