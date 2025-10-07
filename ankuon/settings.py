from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

# Load environment variables from .env
load_dotenv()

# Debugging (remove in production)
# print("SECRET_KEY:", os.getenv('SECRET_KEY'))
# print("DATABASE_URL:", os.getenv('DATABASE_URL'))

# -----------------------------------------------------------------------------
# Base directory
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# Security
# -----------------------------------------------------------------------------
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("The SECRET_KEY setting must not be empty.")

DEBUG = os.getenv('DEBUG', 'True') == 'True'

# In production, replace '*' with your domain, e.g., ['yourdomain.com']
ALLOWED_HOSTS = ['*']

# -----------------------------------------------------------------------------
# Installed apps
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django default apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',

    # Local apps
    'app',  # Your Django app name
]

# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# -----------------------------------------------------------------------------
# URL & WSGI
# -----------------------------------------------------------------------------
ROOT_URLCONF = 'ankuon.urls'
WSGI_APPLICATION = 'ankuon.wsgi.application'

# -----------------------------------------------------------------------------
# Templates
# -----------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
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

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/db.sqlite3'),
        conn_max_age=600
    )
}

# -----------------------------------------------------------------------------
# Password validation
# -----------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -----------------------------------------------------------------------------
# Internationalization
# -----------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# Static files (CSS, JavaScript, Images)
# -----------------------------------------------------------------------------
STATIC_URL = '/static/'

# Where Django will look for static files in development
# Updated to prioritize app/static/assets/ and include ankuon/static if needed
STATICFILES_DIRS = [
    BASE_DIR / 'app' / 'static',  # C:\Users\ankit\OneDrive\Desktop\PORTFOLIO\ankuon\app\static
    BASE_DIR / 'static',  # C:\Users\ankit\OneDrive\Desktop\PORTFOLIO\ankuon\static
]

# Where `collectstatic` will gather files for production
STATIC_ROOT = BASE_DIR / 'staticfiles'

# -----------------------------------------------------------------------------
# Media files (User uploads)
# -----------------------------------------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# -----------------------------------------------------------------------------
# Django REST Framework
# -----------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# -----------------------------------------------------------------------------
# Email configuration
# -----------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# -----------------------------------------------------------------------------
# Cashfree payment configuration
# -----------------------------------------------------------------------------
CASHFREE_APP_ID = os.getenv('CASHFREE_APP_ID', '')
CASHFREE_SECRET_KEY = os.getenv('CASHFREE_SECRET_KEY', '')

# -----------------------------------------------------------------------------
# Celery configuration
# -----------------------------------------------------------------------------
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# -----------------------------------------------------------------------------
# Default primary key field type
# -----------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -----------------------------------------------------------------------------
# Static file usage notes
# -----------------------------------------------------------------------------
# 1. Place assets in app/static/assets/ or static/assets/
#    Example: app/static/assets/ankit.webp or static/assets/ankit.webp
#
# 2. In templates, load static and use:
#    {% load static %}
#    <img src="{% static 'assets/ankit.webp' %}" alt="Ankit">
#
# 3. In production (DEBUG=False), run:
#    python manage.py collectstatic
#
# 4. Verify detection with:
#    python manage.py findstatic assets/ankit.webp
# -----------------------------------------------------------------------------
