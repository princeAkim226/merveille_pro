# Merveille Pro

Application desktop de gestion commerciale — **Flutter (Windows)** + **Django REST** + **PostgreSQL**.

## Démarrage rapide

### Backend
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

### Frontend
```bash
flutter pub get
flutter run -d windows
```

**Comptes démo :** `admin` / `admin123` ou `vendeur` / `vendeur123`

Consultez [INSTALLATION.md](INSTALLATION.md) pour la configuration PostgreSQL et les détails complets.
