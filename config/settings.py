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

# ---------------------------------------------------------------------------
# Sayt qayerda ishlayapti?
#
#   `manzil.txt` fayli BOR      -> ochiq internetdagi server (PythonAnywhere).
#                                  DEBUG o'chadi, faqat o'sha domen qabul
#                                  qilinadi, cookie lar HTTPS ga bog'lanadi.
#   `manzil.txt` fayli YO'Q     -> hammasi eskisidek: mijozning kompyuterida,
#                                  localhost, DEBUG yoqiq.
#
# Fayl ichida bitta qator - domen nomi, masalan:
#     mrclayd12.pythonanywhere.com
# (`https://` yozilsa ham, oxirida `/` bo'lsa ham to'g'ri o'qiladi.)
# ---------------------------------------------------------------------------
_MANZIL_FAYLI = BASE_DIR / "manzil.txt"
TASHQI_MANZIL = ""
if _MANZIL_FAYLI.exists():
    TASHQI_MANZIL = (_MANZIL_FAYLI.read_text(encoding="utf-8").strip()
                     .removeprefix("https://").removeprefix("http://")
                     .rstrip("/").strip())

if TASHQI_MANZIL:
    DEBUG = False
    ALLOWED_HOSTS = [TASHQI_MANZIL]
    CSRF_TRUSTED_ORIGINS = [f"https://{TASHQI_MANZIL}"]

    # PythonAnywhere HTTPS ni o'zi tugatadi va so'rovni ichkariga HTTP bilan
    # uzatadi - shu sarlavha bo'lmasa Django ulanishni xavfsiz deb bilmaydi.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

    # HTTP bilan kelgan so'rov HTTPS ga burib yuboriladi. Bu muhim, chunki
    # qurilma kaliti HAR BIR so'rovning sarlavhasida yuriladi - bir marta
    # ochiq ketsa, kalit sizib chiqadi.
    #
    # DIQQAT: shu sababli telefondagi ilovada manzil ALBATTA `https://` bilan
    # yozilishi kerak. `http://` yozilsa ilova ulanish paytidayoq xato beradi
    # (burilgan so'rov POST bo'lmay qoladi) - jimgina buzilmaydi.
    SECURE_SSL_REDIRECT = True

    # Brauzerga "bu saytga faqat HTTPS bilan kir" deb aytadi (1 yil).
    # Quyi domenlarga tarqatilmaydi - `*.pythonanywhere.com` boshqalarniki.
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

    # Yuqoridagi ikkitasi ATAYLAB False. `manage.py check --deploy` ularni
    # ogohlantirish deb ko'rsatadi - jim qilinadi, aks holda haqiqiy muammo
    # paydo bo'lganda ko'zga tashlanmay qoladi.
    SILENCED_SYSTEM_CHECKS = ["security.W005", "security.W021"]
else:
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
    "sms",       # oylik to'lov eslatmasi (pastdagi sozlamalar bilan YOQILADI)
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

# Mahalliy tizimda (faqat shu kompyuterda) foydalanuvchilar juda kam, shuning
# uchun parol qoidalari yengil. Sayt ochiq internetga chiqqanda esa qoidalar
# kuchayadi - 8 belgi, ommabop parollar va faqat raqamdan iborati taqiqlanadi.
#
# DIQQAT: bu qoidalar faqat YANGI parol qo'yilganda tekshiriladi. Eskidan
# qolgan qisqa parol (masalan `admin`) o'zi bekor bo'lmaydi - uni qo'lda
# almashtirish kerak.
if TASHQI_MANZIL:
    AUTH_PASSWORD_VALIDATORS = [
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
         "OPTIONS": {"min_length": 8}},
        {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]
else:
    AUTH_PASSWORD_VALIDATORS = [
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
         "OPTIONS": {"min_length": 4}},
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
    # Test mijozi HTTP bilan so'raydi - burish yoqiq bo'lsa hamma test 301
    # oladi. Shuning uchun serverda ham (`manzil.txt` bor joyda) testlar
    # xuddi mahalliy kompyuterdagidek ishlaydi.
    SECURE_SSL_REDIRECT = False

# --- Loyihaga xos sozlamalar ---
_VERSIYA_FAYLI = BASE_DIR / "versiya.txt"
SAYT_VERSIYA = (_VERSIYA_FAYLI.read_text(encoding="utf-8").strip()
                if _VERSIYA_FAYLI.exists() else "")

SAYT_NOMI = "Biologiya kursi"
SAYT_TAGLINE = "Moliyaviy boshqaruv tizimi"

# ==========================================================================
# SMS ESLATMA  (menyudagi "Xabarnoma" bo'limi)
# ==========================================================================
# Har oyning 1-sanasida qarzdor o'quvchilarning ota-onasiga "farzandingiz
# uchun kurs to'lovini amalga oshiring" mazmunidagi eslatma NAVBATGA
# yoziladi. Saytning o'zi SMS jo'natmaydi: admin qaysi telefon va qaysi
# SIM kartadan yuborishni tanlaydi, xabarlar o'sha qurilmalarga teng
# bo'linadi va telefondagi "Kurs SMS" ilovasi ularni jo'natadi.
#
# --------------------------- ISH TARTIBI ---------------------------------
#   1) Menyudagi "Xabarnoma" bo'limiga kiring va ulanish kodini oling.
#   2) Telefondagi "Kurs SMS" ilovasiga sayt manzili va shu kodni kiriting.
#   3) Har oyning 1-sanasida navbat o'zi tayyorlanadi (Task Scheduler:
#      python manage.py sms_eslatma). SMS lar esa admin "Xabarlar"
#      bo'limida qurilma/SIM tanlab "Yuborish" ni bosgandan keyin ketadi.
#   O'CHIRISH: quyidagi SMS_ESLATMA_YOQILGAN ni False qiling - bo'lim
#   menyudan ham, manzillardan ham yo'qoladi.
#   Batafsil: sms/API.md
# --------------------------------------------------------------------------

SMS_ESLATMA_YOQILGAN = True

# Xabar kimga ketsin:  "ota" | "ona" | "ikkalasi"
#   "ota"      - faqat otaning raqamiga
#   "ona"      - faqat onaning raqamiga
#   "ikkalasi" - ota va onaning raqamiga alohida-alohida
SMS_KIMGA = "ikkalasi"

# Xabar matni. Ishlatsa bo'ladigan o'rinlar:
#   {oquvchi} {ism} {familiya} {qarz} {kurs} {oy} {oldingi_oy}
# Lotin harflar bilan 160 belgigacha bo'lsa - bitta SMS bo'lib ketadi.
SMS_MATN = (
    "Assalomu alaykum! {oquvchi} uchun kurs to'lovi qarzi: {qarz} so'm. "
    "To'lovni amalga oshirishingizni so'raymiz. {kurs}."
)

# Otaga va onaga alohida matn kerak bo'lsa shu yerga yoziladi.
# Bo'sh qoldirilsa - yuqoridagi umumiy SMS_MATN ishlatiladi.
SMS_MATN_OTA = ""
SMS_MATN_ONA = ""

SMS_YUBORISH_KUNI = 1        # oyning nechanchi sanasida yoziladi
SMS_KECHIKISH_KUNI = 10      # kompyuter o'chiq bo'lsa, necha kungacha kech yozish mumkin
SMS_ENG_KAM_QARZ = 1000      # shu summadan kichik qarz uchun SMS yozilmaydi

SMS_URINISHLAR_CHEGARASI = 3     # ilova bitta xabarga necha marta urinib ko'rsin
SMS_QAYTA_BERISH_DAQIQASI = 30   # ilova olib javob qaytarmasa, shuncha vaqtdan keyin qayta beriladi
SMS_BIR_MARTADA = 20             # API bitta so'rovda nechta xabar bersin

# Sinov uchun: bo'sh bo'lmasa, BARCHA xabarlar ota-onaga emas, shu raqamga
# ketadi. Haqiqiy ishga tushirishdan oldin albatta bo'shatib qo'ying.
SMS_TEST_RAQAM = ""

# Telefondagi ilovaning eng yangi versiyasi. Ilova o'zini shu bilan
# solishtiradi va eskirgan bo'lsa foydalanuvchini ogohlantiradi
# (saytning versiya.txt mantig'i bilan bir xil). Yangi APK chiqarilganda
# shu raqam ham yangilanadi.
SMS_ILOVA_VERSIYA = "1.1.0"

# Oflayn qurilmada qotib qolgan xabarlar shuncha daqiqadan keyin
# navbatga qaytariladi va boshqa qurilmaga berilishi mumkin.
SMS_BOSATISH_DAQIQA = 120
