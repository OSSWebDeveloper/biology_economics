"""
Biologiya kursi - moliyaviy boshqaruv tizimi.
Django sozlamalari.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# XAVFSIZLIK: o'rnatishda `manage.py boshlangich` maxfiy_kalit.txt faylini
# yaratadi va shu yerdan o'qiladi. Fayl bo'lmasa - ishlab chiqish kaliti.
_KALIT_FAYLI = BASE_DIR / "maxfiy_kalit.txt"
if _KALIT_FAYLI.exists() and _KALIT_FAYLI.read_text(encoding="utf-8").strip():
    SECRET_KEY = _KALIT_FAYLI.read_text(encoding="utf-8").strip()
else:
    SECRET_KEY = "django-insecure-bio-moliya-faqat-ishlab-chiqish-uchun-2026"

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "accounts.admin_apps.BoshqaruvAdminConfig",  # Django admin (faqat superuser)
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # loyiha ilovalari
    "accounts",
    "students",
    "payments",
    "staff",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Butun sayt login talab qiladi (@login_not_required bilan istisno qilinadi)
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "dashboard.context_processors.sayt_konteksti",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_USER_MODEL = "accounts.Foydalanuvchi"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 5}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Sayt admin paneli uchun kirish manzillari (Django admin'dan ALOHIDA)
LOGIN_URL = "accounts:kirish"
LOGIN_REDIRECT_URL = "dashboard:bosh"
LOGOUT_REDIRECT_URL = "accounts:kirish"

SESSION_COOKIE_AGE = 60 * 60 * 12          # 12 soat
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_NAME = "bio_sayt_sessiya"   # Django admin sessiyasi bilan bir xil cookie

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

# Testlar tez ishlashi uchun (faqat `manage.py test` paytida)
if "test" in sys.argv:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# --- Loyihaga xos sozlamalar ---
_VERSIYA_FAYLI = BASE_DIR / "versiya.txt"
SAYT_VERSIYA = (_VERSIYA_FAYLI.read_text(encoding="utf-8").strip()
                if _VERSIYA_FAYLI.exists() else "")

SAYT_NOMI = "Biologiya kursi"
SAYT_TAGLINE = "Moliyaviy boshqaruv tizimi"
