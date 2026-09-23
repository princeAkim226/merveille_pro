#!/bin/sh
set -eu
echo "[merveille] waiting for supabase-db"
until pg_isready -h supabase-db -U postgres; do sleep 2; done
echo "[merveille] connected"

psql -h supabase-db -U postgres -v ON_ERROR_STOP=1 <<EOF
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'merveille_app') THEN
    CREATE ROLE merveille_app LOGIN PASSWORD '${DB_PASS}';
  ELSE
    ALTER ROLE merveille_app WITH PASSWORD '${DB_PASS}';
  END IF;
END
\$\$;
-- Required on Supabase so postgres can assign ownership
GRANT merveille_app TO postgres;
EOF

EXISTS=$(psql -h supabase-db -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='merveille'" | tr -d '[:space:]')
echo "[merveille] exists_check='${EXISTS}'"
if [ "$EXISTS" != "1" ]; then
  echo "[merveille] creating database"
  psql -h supabase-db -U postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE merveille"
fi

psql -h supabase-db -U postgres -v ON_ERROR_STOP=1 -c "ALTER DATABASE merveille OWNER TO merveille_app"
psql -h supabase-db -U postgres -v ON_ERROR_STOP=1 -c "GRANT ALL PRIVILEGES ON DATABASE merveille TO merveille_app"

psql -h supabase-db -U postgres -d merveille -v ON_ERROR_STOP=1 <<EOF
GRANT ALL ON SCHEMA public TO merveille_app;
GRANT CREATE ON SCHEMA public TO merveille_app;
ALTER SCHEMA public OWNER TO merveille_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO merveille_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO merveille_app;
EOF

echo "[merveille] verify as merveille_app"
PGPASSWORD="${DB_PASS}" psql -h supabase-db -U merveille_app -d merveille -v ON_ERROR_STOP=1 -c "SELECT current_database(), current_user;"
echo MERVEILLE_DB_READY
sleep 90
