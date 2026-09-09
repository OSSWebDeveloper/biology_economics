from datetime import date

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.permissions import admin_talab
from payments.models import Usul
from payments.services import oy_boshi, oy_nomi

from .forms import MaoshForm, XodimForm, XodimTolovForm
from .models import Xodim, XodimTranzaksiya
from .services import (
    joriy_oy_avansi,
    maosh_summasi,
    maoshlarni_yangila,
    qoldiq_bilan,
    qoldiq_holati,
)


def _qaytish_manzili(request, standart):
    keyingi = request.POST.get("keyingi") or request.GET.get("keyingi")
    if keyingi and keyingi.startswith("/"):
        return keyingi
    return standart


def xodimlar(request):
    maoshlarni_yangila()

    royxat_turi = request.GET.get("royxat", "faol")
    qidiruv = (request.GET.get("q") or "").strip()

    qs = Xodim.objects.all()
    if royxat_turi == "ketgan":
        qs = qs.filter(faol=False)
    elif royxat_turi != "hammasi":
        qs = qs.filter(faol=True)
    if qidiruv:
        qs = qs.filter(
            Q(ism__icontains=qidiruv) | Q(familiya__icontains=qidiruv)
            | Q(lavozim__icontains=qidiruv) | Q(telefon__icontains=qidiruv)
        )

    qs = qoldiq_bilan(qs)
    royxat = list(qs)
    joriy_davr = oy_boshi(date.today())
    for xodim in royxat:
        xodim.holat_info = qoldiq_holati(xodim.qoldiq_summa)
        xodim.oy_avansi = joriy_oy_avansi(xodim, joriy_davr)

    jamlar = {
        "jami": len(royxat),
        "qarzimiz": sum(x.qoldiq_summa for x in royxat if x.qoldiq_summa > 0),
        "oylik_fond": sum(x.oylik_maosh for x in royxat if x.faol),
    }

    return render(request, "staff/royxat.html", {
        "royxat": royxat,
        "jamlar": jamlar,
        "joriy_oy": oy_nomi(joriy_davr),
        "filtr": {"q": qidiruv, "royxat": royxat_turi},
        "tolov_form": XodimTolovForm(),
    })


def xodim(request, pk):
    obyekt = get_object_or_404(Xodim, pk=pk)
    maoshlarni_yangila()

    tranzaksiyalar = list(obyekt.tranzaksiyalar.select_related("yaratgan")
                          .order_by("sana", "id"))
    yiguvchi = 0
    for tr in tranzaksiyalar:
        yiguvchi += tr.ishorali_summa
        tr.qoldiq = yiguvchi
    tranzaksiyalar.reverse()

    joriy_davr = oy_boshi(date.today())
    return render(request, "staff/xodim.html", {
        "xodim": obyekt,
        "tranzaksiyalar": tranzaksiyalar,
        "qoldiq": yiguvchi,
        "holat": qoldiq_holati(yiguvchi),
        "oy_avansi": joriy_oy_avansi(obyekt, joriy_davr),
        "joriy_oy": oy_nomi(joriy_davr),
        "tolov_form": XodimTolovForm(xodim=obyekt),
        "maosh_form": MaoshForm(initial={"oylik_maosh": obyekt.oylik_maosh}),
    })


def xodim_oyna(request, pk):
    obyekt = get_object_or_404(Xodim, pk=pk)
    qoldiq = obyekt.qoldiq
    keyingi = request.GET.get("keyingi") or ""
    return render(request, "staff/_oyna.html", {
        "keyingi": keyingi if keyingi.startswith("/") else "",
        "xodim": obyekt,
        "qoldiq": qoldiq,
        "holat": qoldiq_holati(qoldiq),
        "oy_avansi": joriy_oy_avansi(obyekt),
        "oxirgilar": obyekt.tranzaksiyalar.order_by("-sana", "-id")[:6],
        "tolov_form": XodimTolovForm(xodim=obyekt),
    })


@admin_talab
def xodim_saqlash(request, pk=None):
    obyekt = get_object_or_404(Xodim, pk=pk) if pk else None
    form = XodimForm(request.POST or None, instance=obyekt)
    if request.method == "POST" and form.is_valid():
        yangi = form.save()
        maoshlarni_yangila()
        messages.success(request, f"{yangi.toliq_ism} saqlandi.")
        return redirect("staff:xodim", pk=yangi.pk)
    return render(request, "staff/form.html", {
        "form": form,
        "obyekt": obyekt,
        "sarlavha": "Xodimni tahrirlash" if obyekt else "Yangi xodim",
    })


@admin_talab
def maosh_tayinlash(request, pk):
    """Oylik maoshni faqat admin tayinlaydi."""
    obyekt = get_object_or_404(Xodim, pk=pk)
    if request.method != "POST":
        return redirect("staff:xodim", pk=pk)

    form = MaoshForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Maosh summasi noto'g'ri.")
        return redirect("staff:xodim", pk=pk)

    obyekt.oylik_maosh = form.cleaned_data["oylik_maosh"]
    obyekt.save(update_fields=["oylik_maosh"])

    if form.cleaned_data.get("qayta_hisobla"):
        davr = oy_boshi(date.today())
        summa, kunlar = maosh_summasi(obyekt, davr)
        hisob = obyekt.tranzaksiyalar.filter(
            tur=XodimTranzaksiya.Tur.HISOB, davr=davr
        ).first()
        if hisob and summa > 0:
            hisob.summa, hisob.kunlar = summa, kunlar
            hisob.save(update_fields=["summa", "kunlar"])
        elif summa > 0:
            maoshlarni_yangila()

    messages.success(request, f"{obyekt.toliq_ism}ning oyligi tayinlandi.")
    return redirect("staff:xodim", pk=pk)


@admin_talab
def xodim_ishdan_boshatish(request, pk):
    obyekt = get_object_or_404(Xodim, pk=pk)
    if request.method == "POST":
        obyekt.faol = not obyekt.faol
        obyekt.save()
        holat = "ishga qaytarildi" if obyekt.faol else "ishdan bo'shatildi"
        messages.success(request, f"{obyekt.toliq_ism} {holat}.")
    return redirect("staff:xodim", pk=pk)


@admin_talab
def xodim_ochirish(request, pk):
    obyekt = get_object_or_404(Xodim, pk=pk)
    if request.method == "POST":
        ism = obyekt.toliq_ism
        obyekt.delete()
        messages.success(request, f"{ism} va uning to'lovlar tarixi o'chirildi.")
        return redirect("staff:xodimlar")
    return render(request, "staff/ochirish.html", {"xodim": obyekt})


def tolov_qoshish(request, xodim_id):
    obyekt = get_object_or_404(Xodim, pk=xodim_id)
    qaytish = _qaytish_manzili(request, reverse("staff:xodim", args=[obyekt.pk]))
    if request.method != "POST":
        return redirect(qaytish)

    form = XodimTolovForm(request.POST)
    if form.is_valid():
        tranzaksiya = form.save(commit=False)
        tranzaksiya.xodim = obyekt
        tranzaksiya.yaratgan = request.user
        tranzaksiya.save()
        messages.success(
            request,
            f"{obyekt.toliq_ism}: {tranzaksiya.get_tur_display().lower()} - "
            f"{tranzaksiya.summa:,.0f} so'm.".replace(",", " "),
        )
    else:
        xatolar = "; ".join(
            f"{form.fields[m].label if m in form.fields else m}: {' '.join(x)}"
            for m, x in form.errors.items()
        )
        messages.error(request, f"Saqlanmadi. {xatolar}")
    return redirect(qaytish)


@admin_talab
def tolov_ochirish(request, pk):
    tranzaksiya = get_object_or_404(XodimTranzaksiya, pk=pk)
    qaytish = _qaytish_manzili(request, reverse("staff:xodim", args=[tranzaksiya.xodim_id]))
    if request.method == "POST":
        if tranzaksiya.tur == XodimTranzaksiya.Tur.HISOB:
            messages.error(request, "Avtomatik hisoblangan oylikni o'chirib bo'lmaydi.")
        else:
            tranzaksiya.delete()
            messages.success(request, "Yozuv o'chirildi.")
    return redirect(qaytish)


def oylik_tolovlari(request):
    """Xodimlarga berilgan pullar ro'yxati (naqd / plastik alohida)."""
    usul = request.GET.get("usul") or ""
    tur = request.GET.get("tur") or ""
    sanadan = request.GET.get("sanadan") or ""
    sanagacha = request.GET.get("sanagacha") or ""

    qs = XodimTranzaksiya.objects.select_related("xodim", "yaratgan")
    if usul:
        qs = qs.filter(usul=usul)
    if tur:
        qs = qs.filter(tur=tur)
    if sanadan:
        qs = qs.filter(sana__gte=sanadan)
    if sanagacha:
        qs = qs.filter(sana__lte=sanagacha)

    berilgan = qs.filter(tur__in=[XodimTranzaksiya.Tur.AVANS, XodimTranzaksiya.Tur.OYLIK])
    jamlar = {
        "jami": berilgan.aggregate(s=Sum("summa"))["s"] or 0,
        "naqd": berilgan.filter(usul=Usul.NAQD).aggregate(s=Sum("summa"))["s"] or 0,
        "plastik": berilgan.filter(usul=Usul.PLASTIK).aggregate(s=Sum("summa"))["s"] or 0,
        "avans": berilgan.filter(tur=XodimTranzaksiya.Tur.AVANS).aggregate(s=Sum("summa"))["s"] or 0,
    }

    sahifalar = Paginator(qs, 60)
    return render(request, "staff/tolovlar.html", {
        "sahifa": sahifalar.get_page(request.GET.get("sahifa")),
        "jamlar": jamlar,
        "turlar": XodimTranzaksiya.Tur.choices,
        "usullar": Usul.choices,
        "filtr": {"usul": usul, "tur": tur, "sanadan": sanadan, "sanagacha": sanagacha},
    })
