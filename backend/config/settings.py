"""Configuration Django pour Merveille Pro."""
import os
import sys
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Python 3.14 : copie des contextes templates Django 4.2 (admin, etc.)
if sys.version_info >= (3, 14):
  from django.template.context import BaseContext

  def _base_context_copy(self):
    duplicate = self.__class__.__new__(self.__class__)
    duplicate.__dict__ = self.__dict__.copy()
    duplicate.dicts = self.dicts[:]
    return duplicate

  BaseContext.__copy__ = _base_context_copy


def _env_bool(name: str, default: bool = False) -> bool:
  value = os.environ.get(name)
  if value is None:
    return default
  return value.strip().lower() in ('1', 'true', 'yes', 'on')


# ---------------------------------------------------------------------------
# Paramètres généraux
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-changez-en-production')
DEBUG = _env_bool('DEBUG', default=True)

_allowed = os.environ.get('ALLOWED_HOSTS', '').strip()
if _allowed:
  ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()]
elif DEBUG:
  ALLOWED_HOSTS = ['localhost', '127.0.0.1', '10.0.2.2', '*']
else:
  ALLOWED_HOSTS = ['.onrender.com', '.raaga-bf.com', 'merveille.raaga-bf.com']

_csrf = os.environ.get('CSRF_TRUSTED_ORIGINS', '').strip()
if _csrf:
  CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf.split(',') if o.strip()]
elif not DEBUG:
  CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']
else:
  CSRF_TRUSTED_ORIGINS = []

# ---------------------------------------------------------------------------
# Base de données
# Priorité : DATABASE_URL (Render) > SQLite > PostgreSQL local
# ---------------------------------------------------------------------------
USE_SQLITE = _env_bool('USE_SQLITE', default=False)

DB_NAME = os.environ.get('DB_NAME', 'merveille_pro')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')

DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()

if DATABASE_URL:
  import dj_database_url

  DATABASES = {
    'default': dj_database_url.config(
      default=DATABASE_URL,
      conn_max_age=600,
      ssl_require=not DEBUG,
    )
  }
elif USE_SQLITE:
  DATABASES = {
    'default': {
      'ENGINE': 'django.db.backends.sqlite3',
      'NAME': BASE_DIR / 'db.sqlite3',
    }
  }
else:
  DATABASES = {
    'default': {
      'ENGINE': 'django.db.backends.postgresql',
      'NAME': DB_NAME,
      'USER': DB_USER,
      'PASSWORD': DB_PASSWORD,
      'HOST': DB_HOST,
      'PORT': DB_PORT,
    }
  }

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
_cors = os.environ.get('CORS_ALLOWED_ORIGINS', '').strip()
if _cors:
  CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors.split(',') if o.strip()]
else:
  CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
  ]

# En production sur Render : autoriser les clients desktop / mobiles du réseau
# via CORS_ALLOW_ALL_ORIGINS=True (API JWT, pas de cookies navigateur).
CORS_ALLOW_ALL_ORIGINS = _env_bool('CORS_ALLOW_ALL_ORIGINS', default=DEBUG)

# ---------------------------------------------------------------------------
# Django
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
  'django.contrib.admin',
  'django.contrib.auth',
  'django.contrib.contenttypes',
  'django.contrib.sessions',
  'django.contrib.messages',
  'django.contrib.staticfiles',
  'rest_framework',
  'rest_framework_simplejwt',
  'django_filters',
  'corsheaders',
  'apps.shops',
  'apps.users',
  'apps.products',
  'apps.sales',
  'apps.inventory',
  'apps.finance',
  'apps.core',
]

MIDDLEWARE = [
  'django.middleware.security.SecurityMiddleware',
  'whitenoise.middleware.WhiteNoiseMiddleware',
  'corsheaders.middleware.CorsMiddleware',
  'django.contrib.sessions.middleware.SessionMiddleware',
  'django.middleware.common.CommonMiddleware',
  'django.middleware.csrf.CsrfViewMiddleware',
  'django.contrib.auth.middleware.AuthenticationMiddleware',
  'django.contrib.messages.middleware.MessageMiddleware',
  'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
  {
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
      'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
      ],
    },
  },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
  {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
  {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
  {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
  {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Kinshasa'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
  'DEFAULT_AUTHENTICATION_CLASSES': (
    'rest_framework_simplejwt.authentication.JWTAuthentication',
  ),
  'DEFAULT_PERMISSION_CLASSES': (
    'rest_framework.permissions.IsAuthenticated',
  ),
  'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
  'PAGE_SIZE': 20,
  'DEFAULT_FILTER_BACKENDS': (
    'django_filters.rest_framework.DjangoFilterBackend',
    'rest_framework.filters.SearchFilter',
    'rest_framework.filters.OrderingFilter',
  ),
}

SIMPLE_JWT = {
  'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
  'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
  'ROTATE_REFRESH_TOKENS': True,
  'AUTH_HEADER_TYPES': ('Bearer',),
}

# Sécurité HTTPS derrière le proxy Render
if not DEBUG:
  SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
