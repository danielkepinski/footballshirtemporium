# myshop/settings.py
from pathlib import Path
import os
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from decouple import config
import dj_database_url
import ssl

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security / core ---
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = config("DEBUG", cast=bool, default=True)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost").split(",")
HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME", "").strip()
if HEROKU_APP_NAME:
    ALLOWED_HOSTS.append(f"{HEROKU_APP_NAME}.herokuapp.com")
    
#HEROKU
# If HEROKU_APP_NAME is set, add the Heroku app domain to ALLOWED
HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME", "").strip()
if HEROKU_APP_NAME:
    ALLOWED_HOSTS.append(f"{HEROKU_APP_NAME}.herokuapp.com")

#CSRF
_raw_csrf = os.getenv("CSRF_TRUSTED_ORIGINS", "")
if _raw_csrf:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _raw_csrf.split(",")]
elif HEROKU_APP_NAME:
    CSRF_TRUSTED_ORIGINS = [f"https://{HEROKU_APP_NAME}.herokuapp.com"]

# Security settings for production
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# --- Apps ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "shop.apps.ShopConfig",
    "cart.apps.CartConfig",
    "orders.apps.OrdersConfig",
    "payment.apps.PaymentConfig",
    "accounts",
    "addresses",
]

# --- Middleware ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "myshop.urls"

# --- Templates ---
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "cart.context_processors.cart",
            ],
        },
    },
]

WSGI_APPLICATION = "myshop.wsgi.application"

# --- Database ---
# Default: SQLite for local dev
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
# If DATABASE_URL is set (Heroku Postgres), use it
if os.getenv("DATABASE_URL"):
    DATABASES["default"] = dj_database_url.parse(
        os.environ["DATABASE_URL"],
        conn_max_age=600,
        ssl_require=True,
    )

# --- Internationalization ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static files ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# WhiteNoise storage (hashed + compressed) in production
if not DEBUG:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }

# --- Media files ---
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- Defaults ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Cart ---
CART_SESSION_ID = "cart"

# --- Stripe ---
STRIPE_PUBLISHABLE_KEY = config("STRIPE_PUBLISHABLE_KEY", default="").strip()
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="").strip()
STRIPE_API_VERSION = "2024-04-10"
STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET", default="").strip()

# --- Celery ---
REDIS_URL = config("REDIS_TLS_URL", default=config("REDIS_URL", default="")).strip()

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default=REDIS_URL).strip()
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default=CELERY_BROKER_URL).strip()

# If using TLS (rediss://), configure SSL for Celery
if CELERY_BROKER_URL.startswith("rediss://"):
    CELERY_BROKER_USE_SSL = {"ssl_cert_reqs": ssl.CERT_NONE}
if CELERY_RESULT_BACKEND.startswith("rediss://"):
    CELERY_REDIS_BACKEND_USE_SSL = {"ssl_cert_reqs": ssl.CERT_NONE}

# Keep the app responsive even if worker/backends wobble
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Optional: run tasks inline while stabilizing workers (turn off later)
CELERY_TASK_ALWAYS_EAGER = config("CELERY_TASK_ALWAYS_EAGER", cast=bool, default=False)
CELERY_TASK_EAGER_PROPAGATES = config("CELERY_TASK_EAGER_PROPAGATES", cast=bool, default=False)

# --- Email (dev default) ---
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# --- Auth redirects ---
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "home" 

# --- Logging ---
import logging
LOG_LEVEL = "DEBUG" if DEBUG else "INFO"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[{levelname}] {name}: {message}", "style": "{"},
        "verbose": {"format": "[{levelname}] {asctime} {name} | {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "loggers": {
        "payment": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "orders": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "cart": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "shop": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "": {"handlers": ["console"], "level": LOG_LEVEL},  # root
        # "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        # "django.db.backends": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
