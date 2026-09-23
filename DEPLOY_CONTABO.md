# Déploiement Contabo / Coolify — Merveille Pro

## URLs cibles
- API : https://merveille.raaga-bf.com
- Health : https://merveille.raaga-bf.com/api/health/
- APK : https://dl.merveille.raaga-bf.com
- version.json : https://dl.merveille.raaga-bf.com/version.json

## Prérequis DNS (Netlify raaga-bf.com)
Créer deux enregistrements **A** → `109.199.124.31` :
- `merveille`
- `dl.merveille`

## Coolify API
Panel : https://panel.raaga-bf.com  
Le token doit avoir la permission **write** (le token précédent était en lecture seule → 403).

## 1) Base Postgres dédiée (supabase-db existant)

```bash
# Trouver le container
docker ps --format '{{.Names}}' | grep -i supabase | grep -i db

# Exemple (adapter le nom exact) :
DB=supabase-db-r8brcpnzrcoig6yk7338hhep

# Générer un mot de passe
PASS=$(openssl rand -hex 24)
echo "PASSWORD=$PASS"

# Créer user + DB (sans toucher sooma/syras/voltify)
docker exec -i "$DB" psql -U postgres <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'merveille_app') THEN
    CREATE ROLE merveille_app LOGIN PASSWORD '$PASS';
  END IF;
END
\$\$;
SELECT 'CREATE DATABASE merveille OWNER merveille_app'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'merveille')\gexec
GRANT ALL PRIVILEGES ON DATABASE merveille TO merveille_app;
SQL

docker exec -i "$DB" psql -U postgres -d merveille -c "GRANT ALL ON SCHEMA public TO merveille_app;"
```

`DATABASE_URL` :
```text
postgresql://merveille_app:PASSWORD@HOST_INTERNE_DB:5432/merveille
```
Le hostname interne est souvent le nom du container DB sur le réseau supabase.

## 2) Projet Coolify « Merveille »
Créer manuellement (UI) ou via API write :
- Application **merveille-api** : Dockerfile, root `backend/`, domaine `merveille.raaga-bf.com`
- Application **merveille-dl** : static / nginx, domaine `dl.merveille.raaga-bf.com`, volume `dl/`

Réseaux additionnels pour l’API : `coolify` + réseau supabase (comme Sooma).

Variables API :
```
SECRET_KEY=...
DEBUG=False
ALLOWED_HOSTS=merveille.raaga-bf.com
CSRF_TRUSTED_ORIGINS=https://merveille.raaga-bf.com
CORS_ALLOW_ALL_ORIGINS=True
DATABASE_URL=postgresql://merveille_app:...@...:5432/merveille
RUN_SEED=true
```
Après premier boot réussi : `RUN_SEED=false`.

## 3) Build APK
```bash
flutter build apk --release
copy build\app\outputs\flutter-apk\app-release.apk dl\apk\merveille-pro.apk
```
Mettre à jour `dl/version.json` puis redeploy **merveille-dl**.

## 4) Vérifications (ne pas casser les autres)
```bash
curl -fsS https://merveille.raaga-bf.com/api/health/
curl -fsS https://dl.merveille.raaga-bf.com/version.json
curl -fsS https://voltify.raaga-bf.com/health || true
curl -fsS https://dl.raaga-bf.com/ || true
# Sooma / Syrah : adapter les URLs health connues
```

## 5) Backup Postgres
Ajouter un dump `merveille` au cron existant, sans modifier les dumps sooma/syras :
```bash
docker exec "$DB" pg_dump -U postgres -d merveille -Fc -f /tmp/merveille.dump
```
