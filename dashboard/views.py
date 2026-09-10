from django.shortcuts import render

from accounts.permissions import admin_talab

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
    """Bosh sahifa. Admin va o'qituvchi uchun boshqa-boshqa ko'rinish."""
    barcha_hisoblarni_yangila()
    maoshlarni_yangila()

    if not request.user.admin_mi:
        return _oqituvchi_bosh(request)

    return render(request, "dashboard/bosh.html", {
        "holat": bugungi_holat(),
        "qarzdorlik": qarzdorlik_holati(),
        "qarzdorlar": top_qarzdorlar(),
        "oxirgi_tolovlar": (
            Tranzaksiya.objects.filter(tur=Tranzaksiya.Tur.TOLOV)
            .select_related("oquvchi")[:10]
        ),
    })


@admin_talab
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


def _oqituvchi_bosh(request):
    """O'qituvchining bosh sahifasi: faqat o'z guruhlari va o'quvchilari."""
    from payments.services import balans_bilan, balans_holati
    from students.models import Oquvchi

    guruhlar = []
    for guruh in request.user.guruhlari.filter(faol=True):
        oquvchilar = balans_bilan(guruh.oquvchilar.filter(faol=True))
        balanslar = list(oquvchilar.values_list("balans_summa", flat=True))
        guruhlar.append({
            "guruh": guruh,
            "soni": len(balanslar),
            "qarzdorlar": sum(1 for b in balanslar if b < 0),
            "qarz": sum(-b for b in balanslar if b < 0),
        })

    qarzdorlar = (balans_bilan(
        Oquvchi.objects.filter(faol=True, guruh__oqituvchi__foydalanuvchi=request.user)
        .select_related("guruh"))
        .filter(balans_summa__lt=0).order_by("balans_summa")[:10])

    jami_oquvchi = sum(q["soni"] for q in guruhlar)
    return render(request, "dashboard/bosh_oqituvchi.html", {
        "guruhlar": guruhlar,
        "qarzdorlar": qarzdorlar,
        "jami_oquvchi": jami_oquvchi,
        "jami_qarz": sum(q["qarz"] for q in guruhlar),
        "jami_qarzdor": sum(q["qarzdorlar"] for q in guruhlar),
    })
