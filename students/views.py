from datetime import date

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import admin_talab
from payments.forms import TolovForm
from payments.models import Tranzaksiya
from payments.services import (
    balans_bilan,
    balans_holati,
    barcha_hisoblarni_yangila,
    hisoblarni_yarat,
    holat_filtri,
    oy_boshi,
    oyni_qayta_hisobla,
)

from .forms import ChiqarishForm, GuruhForm, OquvchiForm, QaytarishForm
from .models import Guruh, Oquvchi


def _koradigan_oquvchilar(foydalanuvchi):
    """Admin hammasini, o'qituvchi esa faqat o'z guruhlaridagilarni ko'radi."""
    qs = Oquvchi.objects.select_related("guruh")
    if not foydalanuvchi.admin_mi:
        qs = qs.filter(guruh__oqituvchi=foydalanuvchi)
    return qs


def oquvchilar(request):
    """Kursga keladiganlar ro'yxati + to'lov holati bo'yicha filtr."""
    barcha_hisoblarni_yangila()

    royxat_turi = request.GET.get("royxat", "faol")
    qidiruv = (request.GET.get("q") or "").strip()
    guruh_id = request.GET.get("guruh") or ""
    holat = request.GET.get("holat") or ""
    tartib = request.GET.get("tartib") or "ism"

    qs = _koradigan_oquvchilar(request.user)
    if royxat_turi == "chiqarilgan":
        qs = qs.filter(faol=False)
    elif royxat_turi != "hammasi":
        qs = qs.filter(faol=True)

    if qidiruv:
        qs = qs.filter(
            Q(ism__icontains=qidiruv) | Q(familiya__icontains=qidiruv)
            | Q(telefon__icontains=qidiruv) | Q(ota_telefon__icontains=qidiruv)
            | Q(ona_telefon__icontains=qidiruv)
        )
    if guruh_id.isdigit():
        qs = qs.filter(guruh_id=int(guruh_id))

    qs = holat_filtri(balans_bilan(qs), holat)

    tartiblar = {
        "ism": ["familiya", "ism"],
        "balans": ["balans_summa"],
        "balans_teskari": ["-balans_summa"],
        "yangi": ["-boshlangan_sana"],
    }
    qs = qs.order_by(*tartiblar.get(tartib, tartiblar["ism"]))

    sahifalar = Paginator(qs, 50)
    sahifa = sahifalar.get_page(request.GET.get("sahifa"))

    for oquvchi in sahifa:
        oquvchi.holat_info = balans_holati(oquvchi.balans_summa)

    balanslar = list(qs.values_list("balans_summa", flat=True))
    jamlar = {
        "jami": len(balanslar),
        "qarzdor": sum(1 for b in balanslar if b < 0),
        "oldindan": sum(1 for b in balanslar if b > 0),
    }

    return render(request, "students/royxat.html", {
        "sahifa": sahifa,
        "guruhlar": request.user.guruhlari.filter(faol=True),
        "jamlar": jamlar,
        "filtr": {"q": qidiruv, "guruh": guruh_id, "holat": holat,
                  "royxat": royxat_turi, "tartib": tartib},
        "tolov_form": TolovForm(),
    })


def oquvchi(request, pk):
    """O'quvchining to'liq kartochkasi: hisob-kitob tarixi."""
    obyekt = get_object_or_404(_koradigan_oquvchilar(request.user), pk=pk)
    hisoblarni_yarat(obyekt)

    tranzaksiyalar = list(obyekt.tranzaksiyalar.select_related("yaratgan")
                          .order_by("sana", "id"))
    yiguvchi = 0
    for tr in tranzaksiyalar:
        yiguvchi += tr.ishorali_summa
        tr.qoldiq = yiguvchi
    tranzaksiyalar.reverse()

    balans = yiguvchi
    return render(request, "students/oquvchi.html", {
        "oquvchi": obyekt,
        "tranzaksiyalar": tranzaksiyalar,
        "balans": balans,
        "holat": balans_holati(balans),
        "tolov_form": TolovForm(),
        "chiqarish_form": ChiqarishForm(),
        "qaytarish_form": QaytarishForm(),
    })


def oquvchi_saqlash(request, pk=None):
    obyekt = (get_object_or_404(_koradigan_oquvchilar(request.user), pk=pk)
              if pk else None)
    form = OquvchiForm(request.POST or None, instance=obyekt,
                       foydalanuvchi=request.user)
    if request.method == "POST" and form.is_valid():
        yangi = form.save()
        hisoblarni_yarat(yangi)
        messages.success(request, f"{yangi.toliq_ism} saqlandi.")
        return redirect("students:oquvchi", pk=yangi.pk)
    return render(request, "students/form.html", {
        "form": form,
        "obyekt": obyekt,
        "sarlavha": "O'quvchini tahrirlash" if obyekt else "Yangi o'quvchi qo'shish",
    })


def oquvchi_chiqarish(request, pk):
    """Kursga keladiganlar ro'yxatidan chiqarish (tarix saqlanib qoladi)."""
    obyekt = get_object_or_404(_koradigan_oquvchilar(request.user), pk=pk)
    if request.method != "POST":
        return redirect("students:oquvchi", pk=pk)

    form = ChiqarishForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Chiqarish sanasi noto'g'ri.")
        return redirect("students:oquvchi", pk=pk)

    sana = form.cleaned_data["chiqarilgan_sana"]
    obyekt.faol = False
    obyekt.chiqarilgan_sana = sana
    obyekt.chiqarish_sababi = form.cleaned_data.get("sabab", "")
    obyekt.save()

    # Chiqarilgan sanadan keyingi oylarning hisoblarini olib tashlaymiz
    obyekt.tranzaksiyalar.filter(
        tur=Tranzaksiya.Tur.HISOB, davr__gt=oy_boshi(sana)
    ).delete()

    # Tugallanmagan oy o'sha zahoti hisoblanadi - qatnashgan kunlari uchun
    oyni_qayta_hisobla(obyekt, oy_boshi(sana), sana)

    messages.success(request, f"{obyekt.toliq_ism} ro'yxatdan chiqarildi.")
    return redirect("students:oquvchi", pk=pk)


def oquvchi_qaytarish(request, pk):
    obyekt = get_object_or_404(_koradigan_oquvchilar(request.user), pk=pk)
    if request.method != "POST":
        return redirect("students:oquvchi", pk=pk)

    form = QaytarishForm(request.POST)
    sana = form.cleaned_data["boshlangan_sana"] if form.is_valid() else date.today()
    obyekt.faol = True
    obyekt.boshlangan_sana = sana
    obyekt.chiqarish_sababi = ""
    obyekt.save()
    hisoblarni_yarat(obyekt)
    messages.success(request, f"{obyekt.toliq_ism} ro'yxatga qaytarildi.")
    return redirect("students:oquvchi", pk=pk)


@admin_talab
def oquvchi_ochirish(request, pk):
    """Butunlay o'chirish - barcha moliyaviy tarixi bilan (faqat admin)."""
    obyekt = get_object_or_404(Oquvchi, pk=pk)
    if request.method == "POST":
        ism = obyekt.toliq_ism
        obyekt.delete()
        messages.success(request, f"{ism} va uning butun tarixi o'chirildi.")
        return redirect("students:oquvchilar")
    return render(request, "students/ochirish.html", {"oquvchi": obyekt})


# ---------------------------------------------------------------- guruhlar

def guruhlar(request):
    royxat = request.user.guruhlari.select_related("oqituvchi").annotate(
        oquvchilar_soni=Count("oquvchilar", filter=Q(oquvchilar__faol=True))
    )
    return render(request, "students/guruhlar.html", {"royxat": royxat})


def guruh_oyna(request, pk):
    """Guruh ustiga bosilganda ochiladigan oynacha: guruhdagi o'quvchilar."""
    guruh = get_object_or_404(request.user.guruhlari.select_related("oqituvchi"), pk=pk)
    oquvchilar = list(
        balans_bilan(guruh.oquvchilar.filter(faol=True)).order_by("familiya", "ism")
    )
    for oquvchi in oquvchilar:
        oquvchi.holat_info = balans_holati(oquvchi.balans_summa)

    qarz = sum(-o.balans_summa for o in oquvchilar if o.balans_summa < 0)
    keyingi = request.GET.get("keyingi") or ""
    return render(request, "students/_guruh_oyna.html", {
        "guruh": guruh,
        "oquvchilar": oquvchilar,
        "qarzdorlar": sum(1 for o in oquvchilar if o.balans_summa < 0),
        "qarz": qarz,
        "keyingi": keyingi if keyingi.startswith("/") else "",
    })


@admin_talab
def guruh_saqlash(request, pk=None):
    obyekt = get_object_or_404(Guruh, pk=pk) if pk else None
    form = GuruhForm(request.POST or None, instance=obyekt,
                     foydalanuvchi=request.user)
    if request.method == "POST" and form.is_valid():
        guruh = form.save(commit=False)
        if guruh.oqituvchi is None:
            # O'qituvchi tanlanmasa, guruhni yaratgan admin o'qituvchi bo'ladi
            guruh.oqituvchi = request.user
        guruh.save()
        messages.success(request, "Guruh saqlandi.")
        return redirect("students:guruhlar")
    return render(request, "students/guruh_form.html", {
        "form": form,
        "obyekt": obyekt,
        "sarlavha": "Guruhni tahrirlash" if obyekt else "Yangi guruh",
    })


@admin_talab
def guruh_ochirish(request, pk):
    obyekt = get_object_or_404(Guruh, pk=pk)
    if request.method == "POST":
        obyekt.delete()
        messages.success(request, "Guruh o'chirildi (o'quvchilar guruhsiz qoldi).")
    return redirect("students:guruhlar")
