from pathlib import Path
import os

from dotenv import load_dotenv
import dj_database_url


# Load .env locally
load_dotenv()


# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


# =====================================================
# SECURITY
# =====================================================

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY is missing")


DEBUG = os.getenv("DEBUG", "False") == "True"


ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1"
).split(",")


CSRF_TRUSTED_ORIGINS = [
    "https://ankuon.onrender.com",
]


# Render HTTPS support
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

USE_X_FORWARDED_HOST = True



# =====================================================
# APPLICATIONS
# =====================================================

INSTALLED_APPS = [

    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third party
    "rest_framework",

    # Local apps
    "app",
]



# =====================================================
# MIDDLEWARE
# =====================================================

MIDDLEWARE = [

    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]



# =====================================================
# URL CONFIG
# =====================================================

ROOT_URLCONF = "ankuon.urls"

WSGI_APPLICATION = "ankuon.wsgi.application"



# =====================================================
# TEMPLATES
# =====================================================

TEMPLATES = [

    {
        "BACKEND":
        "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {

            "context_processors": [

                "django.template.context_processors.debug",

                "django.template.context_processors.request",

                "django.contrib.auth.context_processors.auth",

                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]



# =====================================================
# DATABASE
# =====================================================

DATABASES = {

    "default": dj_database_url.config(

        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",

        conn_max_age=600,

    )
}



# =====================================================
# PASSWORD VALIDATION
# =====================================================

AUTH_PASSWORD_VALIDATORS = [

    {
        "NAME":
        "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },

    {
        "NAME":
        "django.contrib.auth.password_validation.MinimumLengthValidator",
    },

    {
        "NAME":
        "django.contrib.auth.password_validation.CommonPasswordValidator",
    },

    {
        "NAME":
        "django.contrib.auth.password_validation.NumericPasswordValidator",
    },

]



# =====================================================
# LANGUAGE
# =====================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True



# =====================================================
# STATIC FILES
# =====================================================

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"


STATICFILES_DIRS = []


if (BASE_DIR / "static").exists():

    STATICFILES_DIRS.append(
        BASE_DIR / "static"
    )


if (BASE_DIR / "app" / "static").exists():

    STATICFILES_DIRS.append(
        BASE_DIR / "app" / "static"
    )



STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedStaticFilesStorage"
)



# =====================================================
# MEDIA FILES
# =====================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"



# =====================================================
# DJANGO REST FRAMEWORK
# =====================================================

REST_FRAMEWORK = {

    "DEFAULT_AUTHENTICATION_CLASSES": [

        "rest_framework.authentication.SessionAuthentication",

    ],

}



# =====================================================
# EMAIL
# =====================================================

EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
)


EMAIL_HOST = os.getenv(
    "EMAIL_HOST",
    "smtp.gmail.com"
)


EMAIL_PORT = int(
    os.getenv(
        "EMAIL_PORT",
        587
    )
)


EMAIL_USE_TLS = (
    os.getenv(
        "EMAIL_USE_TLS",
        "True"
    ) == "True"
)


EMAIL_HOST_USER = os.getenv(
    "EMAIL_HOST_USER",
    ""
)


EMAIL_HOST_PASSWORD = os.getenv(
    "EMAIL_HOST_PASSWORD",
    ""
)



# =====================================================
# CASHFREE
# =====================================================

CASHFREE_APP_ID = os.getenv(
    "CASHFREE_APP_ID",
    ""
)


CASHFREE_SECRET_KEY = os.getenv(
    "CASHFREE_SECRET_KEY",
    ""
)



# =====================================================
# CELERY
# =====================================================

CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    None
)


CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND",
    None
)


CELERY_ACCEPT_CONTENT = [
    "json"
]


CELERY_TASK_SERIALIZER = "json"



# =====================================================
# DEFAULT PRIMARY KEY
# =====================================================

DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)