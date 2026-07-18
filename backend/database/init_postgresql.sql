-- Script d'initialisation PostgreSQL pour Merveille Pro
-- Exécuter en tant que superutilisateur PostgreSQL

CREATE DATABASE merveille_pro
  WITH ENCODING 'UTF8'
  LC_COLLATE = 'French_France.1252'
  LC_CTYPE = 'French_France.1252'
  TEMPLATE template0;

-- Créer un utilisateur dédié (optionnel)
-- CREATE USER merveille_user WITH PASSWORD 'votre_mot_de_passe';
-- GRANT ALL PRIVILEGES ON DATABASE merveille_pro TO merveille_user;

-- Puis adapter backend/config/settings.py (DB_PASSWORD, etc.)
-- et exécuter les migrations Django :
-- python manage.py migrate
-- python manage.py seed_data
