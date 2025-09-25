# settings.py
from pathlib import Path
import os
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "dev-only-insecure-key-change-me"  # reminder to use env var in real deployments
)
DEBUG = config("DEBUG", cast=bool, default=True)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost").split(",")

# APPS
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "shop.apps.ShopConfig",
    "cart.apps.CartConfig",
    'orders.apps.OrdersConfig',
    'payment.apps.PaymentConfig',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "myshop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                'django.template.context_processors.debug',
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                'cart.context_processors.cart',
            ],
        },
    },
]

WSGI_APPLICATION = "myshop.wsgi.application"

# DATABASE
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# INTERNATIONALIZATION
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# STATIC FILES
# URL for static files
STATIC_URL = "static/"
# Where collectstatic will gather files (create this folder)
STATIC_ROOT = BASE_DIR / "staticfiles"
# Optional: additional static sources during development (not used by collectstatic)
STATICFILES_DIRS = [BASE_DIR / "static"]

# MEDIA (uploads) – optional but useful if you have ImageFields
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# DEFAULT PRIMARY KEY TYPE
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

#cart
CART_SESSION_ID = 'cart'

#stripe settings
STRIPE_PUBLISHABLE_KEY = config("STRIPE_PUBLISHABLE_KEY", default="").strip()
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="").strip()
STRIPE_API_VERSION = "2024-04-10"
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET').strip()


#celery
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="amqp://guest:guest@localhost:5672//")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="rpc://")
#CELERY_TASK_ALWAYS_EAGER = False

#in test use 
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Email (dev)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# --- Logging ---
import logging

LOG_LEVEL = "DEBUG" if DEBUG else "INFO"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{levelname}] {name}: {message}",
            "style": "{",
        },
        "verbose": {
            "format": "[{levelname}] {asctime} {name} | {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        # Your apps
        "payment": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "orders":  {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "cart":    {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "shop":    {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},

        # Root logger (everything else)
        "": {"handlers": ["console"], "level": LOG_LEVEL},
        
        # Optional extras (uncomment when needed)
        # "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        # "django.db.backends": {"handlers": ["console"], "level": "WARNING", "propagate": False},  # SQL logs
    },
}
