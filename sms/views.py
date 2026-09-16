"""Admin uchun "Xabarnoma" bo'limi.

  /xabarnoma/            ulanish kodi, ulangan qurilmalar, hodisalar
  /xabarnoma/xabarlar/   navbat, qurilma/SIM tanlash, yuborish
  /xabarnoma/xatolar/    jo'natilmagan xabarlar va qayta urinish

Modul o'chiq bo'lsa (`SMS_ESLATMA_YOQILGAN = False`) bu bo'lim menyuda
ko'rinmaydi va manzillari 404 qaytaradi.
"""
from functools import wraps

from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.permissions import admin_talab

from . import services, sozlamalar
from .models import Bildirishnoma, Qurilma, SimKarta, SmsXabar, UlanishKodi


def yoqilgan_talab(view_func):
    """Modul o'chiq bo'lsa sahifa umuman yo'q."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not sozlamalar.yoqilgan():
            raise Http404("SMS moduli o'chirilgan")
        return view_func(request, *args, **kwargs)

    return wrapper


def _oxirgi_kod():
    return UlanishKodi.objects.filter(ishlatilgan__isnull=True).first()


@admin_talab
@yoqilgan_talab
def bosh(request):
    """Xabarnoma bo'limining bosh sahifasi."""
    services.berilganlarni_bosat()

    qurilmalar = services.qurilmalar_holati()
    kod = _oxirgi_kod()
    if kod is not None and not kod.yaroqli:
        kod = None

    yangi_bildirishnomalar = list(
        Bildirishnoma.objects.select_related("qurilma")[:20]
    )
    Bildirishnoma.objects.filter(korildi=False).update(korildi=True)

    return render(request, "sms/bosh.html", {
        "kod": kod,
        "qurilmalar": qurilmalar,
        "sanoq": services.navbat_holati(),
        "bildirishnomalar": yangi_bildirishnomalar,
    })


@admin_talab
@yoqilgan_talab
@require_POST
def kod_yarat(request):
    kod = UlanishKodi.yarat(request.user)
    messages.success(
        request,
        f"Ulanish kodi: {kod.korinish} - {UlanishKodi.AMAL_DAQIQA} daqiqa amal qiladi.",
    )
    return redirect("sms:bosh")


@admin_talab
@yoqilgan_talab
@require_POST
def qurilma_ochir(request, pk):
    """Qurilmani vaqtincha o'chirish yoki qayta yoqish."""
    qurilma = get_object_or_404(Qurilma, pk=pk)
    qurilma.faol = not qurilma.faol
    qurilma.save(update_fields=["faol"])
    if not qurilma.faol:
        # O'chirilgan qurilmadagi xabarlar navbatga qaytsin
        SmsXabar.objects.filter(
            qurilma=qurilma,
            holat__in=[SmsXabar.Holat.BERILDI, SmsXabar.Holat.OLINDI],
        ).update(holat=SmsXabar.Holat.NAVBATDA, qurilma=None, sim=None,
                 berilgan=None, olingan=None)
    messages.success(
        request,
        f"{qurilma.nomi} " + ("yoqildi." if qurilma.faol else "o'chirildi."),
    )
    return redirect("sms:bosh")


@admin_talab
@yoqilgan_talab
@require_POST
def qurilma_uzish(request, pk):
    """Qurilmani butunlay uzish - qaytadan 12 xonalik kod bilan ulanadi."""
    qurilma = get_object_or_404(Qurilma, pk=pk)
    nomi = qurilma.nomi
    SmsXabar.objects.filter(
        qurilma=qurilma,
        holat__in=[SmsXabar.Holat.BERILDI, SmsXabar.Holat.OLINDI],
    ).update(holat=SmsXabar.Holat.NAVBATDA, qurilma=None, sim=None,
             berilgan=None, olingan=None)
    qurilma.delete()
    Bildirishnoma.qosh(Bildirishnoma.Turi.UZILDI, f"{nomi} saytdan uzildi")
    messages.success(request, f"{nomi} uzildi.")
    return redirect("sms:bosh")


@admin_talab
@yoqilgan_talab
@require_POST
def sim_ochir(request, pk):
    """SIM kartani yuborishdan chiqarib qo'yish yoki qaytarish."""
    sim = get_object_or_404(SimKarta.objects.select_related("qurilma"), pk=pk)
    sim.faol = not sim.faol
    sim.save(update_fields=["faol"])
    return redirect("sms:bosh")


@admin_talab
@yoqilgan_talab
def xabarlar(request):
    """Navbat, qurilma tanlash va yuborish."""
    services.berilganlarni_bosat()

    qurilmalar = services.qurilmalar_holati()
    navbat = (SmsXabar.objects
              .filter(holat=SmsXabar.Holat.NAVBATDA)
              .select_related("oquvchi")
              .order_by("oquvchi__familiya", "oquvchi__ism")[:200])
    jarayonda = (SmsXabar.objects
                 .filter(holat__in=[SmsXabar.Holat.BERILDI, SmsXabar.Holat.OLINDI])
                 .select_related("oquvchi", "qurilma", "sim")
                 .order_by("qurilma", "id")[:200])

    return render(request, "sms/xabarlar.html", {
        "qurilmalar": qurilmalar,
        "navbat": navbat,
        "navbat_soni": SmsXabar.objects.filter(holat=SmsXabar.Holat.NAVBATDA).count(),
        "jarayonda": jarayonda,
        "sanoq": services.navbat_holati(),
    })


@admin_talab
@yoqilgan_talab
@require_POST
def yuborish(request):
    """Tanlangan qurilma/SIM larga xabarlarni teng taqsimlaydi."""
    sim_pklari = request.POST.getlist("sim")
    qurilma_pklari = request.POST.getlist("qurilma")

    kanallar = services.kanallar_royxati(sim_pklari, qurilma_pklari)
    if not kanallar:
        messages.error(request, "Hech qanday qurilma tanlanmadi.")
        return redirect("sms:xabarlar")

    oflayn = [q.nomi for q, _ in kanallar if not q.onlayn]
    natija = services.taqsimla(kanallar)

    if not natija["jami"]:
        messages.info(request, "Navbatda yuboriladigan xabar yo'q.")
        return redirect("sms:xabarlar")

    tafsilot = ", ".join(
        f"{qurilma.nomi}{' / ' + sim.nomi if sim else ''}: {soni} ta"
        for qurilma, sim, soni in natija["kanallar"]
    )
    messages.success(
        request,
        f"{natija['jami']} ta xabar yuborishga berildi. {tafsilot}",
    )
    if oflayn:
        messages.warning(
            request,
            "Bu qurilma(lar) hozir oflayn - internetga ulanganda jo'natadi: "
            + ", ".join(sorted(set(oflayn))),
        )
    return redirect("sms:xabarlar")


@admin_talab
@yoqilgan_talab
@require_POST
def navbatni_tayyorla(request):
    """Navbatni qo'lda tayyorlash (odatda 1-sanada o'zi tayyorlanadi)."""
    soni = services.eslatmalarni_navbatga_qoy(majburiy=True)
    if soni:
        messages.success(request, f"{soni} ta yangi eslatma navbatga qo'shildi.")
    else:
        messages.info(request, "Yangi eslatma yo'q - qarzdorlarning hammasi navbatda.")
    return redirect("sms:xabarlar")


@admin_talab
@yoqilgan_talab
def xatolar(request):
    """Jo'natilmagan xabarlar."""
    royxat = (SmsXabar.objects
              .filter(holat=SmsXabar.Holat.XATO)
              .select_related("oquvchi", "qurilma", "sim")
              .order_by("-id")[:300])
    return render(request, "sms/xatolar.html", {
        "royxat": royxat,
        "soni": SmsXabar.objects.filter(holat=SmsXabar.Holat.XATO).count(),
        "sanoq": services.navbat_holati(),
    })


@admin_talab
@yoqilgan_talab
@require_POST
def qayta_urin(request, pk):
    xabar = get_object_or_404(SmsXabar.objects.select_related("qurilma"), pk=pk)
    holat = services.qayta_urin(xabar)
    if holat == SmsXabar.Holat.BERILDI:
        messages.success(request, f"{xabar.telefon} - qayta urinishga berildi.")
    else:
        messages.success(
            request,
            f"{xabar.telefon} - navbatga qaytarildi. \"Xabarlar\" bo'limidan yuboring.",
        )
    return redirect("sms:xatolar")


@admin_talab
@yoqilgan_talab
@require_POST
def hammasini_qayta_urin(request):
    soni = services.hammasini_qayta_urin()
    if soni:
        messages.success(request, f"{soni} ta xabar qayta urinishga qo'yildi.")
    else:
        messages.info(request, "Qayta urinadigan xabar yo'q.")
    return redirect("sms:xatolar")


@admin_talab
@yoqilgan_talab
def holat_json(request):
    """Sahifa o'zini yangilab turishi uchun qisqa holat (JS uchun)."""
    qurilmalar = services.qurilmalar_holati()
    return JsonResponse({
        "qurilmalar": [{
            "id": q.pk,
            "nomi": q.nomi,
            "holat": q.holat_kodi,
            "holat_nomi": q.holat_nomi,
            "aloqa": q.aloqa_matni,
            "batareya": q.batareya,
        } for q in qurilmalar["royxat"]],
        "onlayn": qurilmalar["onlayn"],
        "jami": qurilmalar["jami"],
        "sanoq": services.navbat_holati(),
        "yangi_bildirishnoma": Bildirishnoma.objects.filter(korildi=False).count(),
    })
