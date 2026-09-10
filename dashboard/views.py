from django.shortcuts import render

from payments.models import Tranzaksiya
from payments.services import barcha_hisoblarni_yangila
from staff.services import maoshlarni_yangila

from .services import (
    bugungi_holat,
    davr_chegarasi,
    guruhlar_kesimi,
    moliya_hisoboti,
    oylik_dinamika,
    qarzdorlik_holati,
    top_qarzdorlar,
)


def bosh(request):
    """Bosh sahifa: kunlik holat va tezkor ko'rsatkichlar."""
    barcha_hisoblarni_yangila()
    maoshlarni_yangila()

    return render(request, "dashboard/bosh.html", {
        "holat": bugungi_holat(),
        "qarzdorlik": qarzdorlik_holati(),
        "qarzdorlar": top_qarzdorlar(),
        "oxirgi_tolovlar": (
            Tranzaksiya.objects.filter(tur=Tranzaksiya.Tur.TOLOV)
            .select_related("oquvchi")[:10]
        ),
    })


def moliya(request):
    """Moliya (statistika) bo'limi."""
    kod = request.GET.get("davr", "oy")
    boshi_matn = request.GET.get("sanadan") or None
    oxiri_matn = request.GET.get("sanagacha") or None
    if boshi_matn or oxiri_matn:
        kod = "tanlangan"

    boshi, oxiri, davr_nomi = davr_chegarasi(kod, boshi_matn, oxiri_matn)

    return render(request, "dashboard/moliya.html", {
        "hisobot": moliya_hisoboti(boshi, oxiri),
        "qarzdorlik": qarzdorlik_holati(),
        "dinamika": oylik_dinamika(),
        "guruhlar": guruhlar_kesimi(boshi, oxiri),
        "davr": {"kod": kod, "nom": davr_nomi,
                 "sanadan": boshi_matn or "", "sanagacha": oxiri_matn or ""},
    })
