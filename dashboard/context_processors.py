from django.conf import settings


def sayt_konteksti(request):
    return {
        "SAYT_NOMI": getattr(settings, "SAYT_NOMI", "Kurs moliyasi"),
        "SAYT_TAGLINE": getattr(settings, "SAYT_TAGLINE", ""),
        "SAYT_VERSIYA": getattr(settings, "SAYT_VERSIYA", ""),
    }
