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
EOF

EXISTS=$(psql -h supabase-db -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='merveille'")
if [ "$EXISTS" != "1" ]; then
  echo "[merveille] creating database"
  psql -h supabase-db -U postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE merveille OWNER merveille_app"
else
  echo "[merveille] database already exists"
fi

psql -h supabase-db -U postgres -d merveille -v ON_ERROR_STOP=1 -c "GRANT ALL ON SCHEMA public TO merveille_app"
echo MERVEILLE_DB_READY
sleep 120
