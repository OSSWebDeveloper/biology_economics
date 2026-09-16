"""SMS modulining sozlamalari bitta joyda.

Qiymatlar `config/settings.py` dan olinadi. Sozlama yozilmagan bo'lsa,
shu yerdagi standart qiymat ishlatiladi - ya'ni modul settings.py ga
tegilmasa ham xatosiz ishlaydi (lekin O'CHIQ holatda turadi).
"""
from django.conf import settings

# Standart qiymatlar
YOQILGAN = False
KIMGA = "ikkalasi"          # "ota" | "ona" | "ikkalasi"
YUBORISH_KUNI = 1           # oyning nechanchi sanasida navbat tayyorlanadi
KECHIKISH_KUNI = 10         # kompyuter o'chiq bo'lsa, necha kungacha kech tayyorlash mumkin
ENG_KAM_QARZ = 1000         # shu summadan kichik qarzga SMS yozilmaydi
URINISHLAR_CHEGARASI = 3    # ilova necha marta urinib ko'rsin
BIR_MARTADA = 20            # API bitta so'rovda nechta xabar bersin
BOSATISH_DAQIQA = 120       # oflayn qurilmadan xabarlarni shuncha vaqtdan keyin qaytarib olish

MATN = ("Assalomu alaykum! {oquvchi} uchun kurs to'lovi qarzi: {qarz} so'm. "
        "To'lovni amalga oshirishingizni so'raymiz. {kurs}.")


def _olish(nom, standart):
    qiymat = getattr(settings, nom, None)
    return standart if qiymat is None else qiymat


def yoqilgan():
    """Asosiy kalit. False bo'lsa modul butunlay jim turadi."""
    return bool(_olish("SMS_ESLATMA_YOQILGAN", YOQILGAN))


def kimga():
    """Xabar kimga ketadi: "ota" | "ona" | "ikkalasi"."""
    qiymat = str(_olish("SMS_KIMGA", KIMGA)).strip().lower()
    return qiymat if qiymat in ("ota", "ona", "ikkalasi") else KIMGA


def matn(qabul_qiluvchi=""):
    """Xabar andozasi. Ota va onaga alohida matn yozilgan bo'lsa - o'shanisi."""
    alohida = {"ota": "SMS_MATN_OTA", "ona": "SMS_MATN_ONA"}.get(qabul_qiluvchi)
    if alohida:
        qiymat = str(_olish(alohida, "") or "").strip()
        if qiymat:
            return qiymat
    return str(_olish("SMS_MATN", MATN) or MATN)


def yuborish_kuni():
    return int(_olish("SMS_YUBORISH_KUNI", YUBORISH_KUNI))


def kechikish_kuni():
    return int(_olish("SMS_KECHIKISH_KUNI", KECHIKISH_KUNI))


def eng_kam_qarz():
    return int(_olish("SMS_ENG_KAM_QARZ", ENG_KAM_QARZ))


def urinishlar_chegarasi():
    return int(_olish("SMS_URINISHLAR_CHEGARASI", URINISHLAR_CHEGARASI))


def bir_martada():
    return int(_olish("SMS_BIR_MARTADA", BIR_MARTADA))


def bosatish_daqiqa():
    return int(_olish("SMS_BOSATISH_DAQIQA", BOSATISH_DAQIQA))


def test_raqam():
    """Bo'sh bo'lmasa - BARCHA xabarlar shu raqamga ketadi (sinov uchun)."""
    return str(_olish("SMS_TEST_RAQAM", "") or "").strip()


def kurs_nomi():
    return str(getattr(settings, "SAYT_NOMI", "") or "").strip()


def ilova_versiyasi():
    """Telefondagi ilovaning eng yangi versiyasi.

    Ilova o'zini shu bilan solishtiradi va eskirgan bo'lsa ogohlantiradi
    (saytning `versiya.txt` mantig'i bilan bir xil).
    """
    return str(_olish("SMS_ILOVA_VERSIYA", "") or "").strip()
