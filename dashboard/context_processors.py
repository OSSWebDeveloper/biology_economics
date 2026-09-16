from django.conf import settings

from sms import sozlamalar as sms_sozlama


def sayt_konteksti(request):
    return {
        "SAYT_NOMI": getattr(settings, "SAYT_NOMI", "Kurs moliyasi"),
        "SAYT_TAGLINE": getattr(settings, "SAYT_TAGLINE", ""),
        "SAYT_VERSIYA": getattr(settings, "SAYT_VERSIYA", ""),
        # Menyuda "Xabarnoma" bo'limi ko'rinishi shu bayroqqa bog'liq
        "SMS_YOQILGAN": sms_sozlama.yoqilgan(),
    }
