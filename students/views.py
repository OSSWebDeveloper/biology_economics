from datetime import date

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.permissions import admin_talab
from payments.forms import TolovForm
from payments.models import Tranzaksiya
from payments.services import (
    balans_bilan,
    balans_holati,
    balans_ifodasi,
    barcha_hisoblarni_yangila,
    hisoblarni_yarat,
    holat_filtri,
    oy_boshi,
    oyni_qayta_hisobla,
)

from .forms import ArxivForm, ChiqarishForm, GuruhForm, OquvchiForm, QaytarishForm
from .models import Arxiv, Guruh, Oquvchi


def _koradigan_oquvchilar(foydalanuvchi):
    """Admin hammasini, o'qituvchi esa faqat o'z guruhlaridagilarni ko'radi.

    Arxivlangan o'quvchining guruhi bo'shatiladi, shuning uchun o'qituvchi uni
    arxivdagi guruh yozuvi orqali ko'rishda davom etadi.
    """
    qs = Oquvchi.objects.select_related("guruh")
    if not foydalanuvchi.admin_mi:
        qs = qs.filter(
            Q(guruh__oqituvchi=foydalanuvchi) | Q(arxiv__guruh__oqituvchi=foydalanuvchi)
        )
    return qs


QARZ_ROYXATI = "qarzdor"


def _qamrov_filtri(qs, qamrov):
    """Qarzdorlar bo'limi kimlarni qamrab olishi: faol / chiqarilgan / hammasi."""
    if qamrov == "chiqarilgan":
        return qs.filter(faol=False)
    if qamrov == "hammasi":
        return qs
    return qs.filter(faol=True)


def oquvchilar(request):
    """O'quvchilar ro'yxati: kursga keladiganlar, chiqarilganlar va qarzdorlar."""
    barcha_hisoblarni_yangila()

    royxat_turi = request.GET.get("royxat", "faol")
    qarz_royxati = royxat_turi == QARZ_ROYXATI
    qidiruv = (request.GET.get("q") or "").strip()
    guruh_id = request.GET.get("guruh") or ""
    holat = request.GET.get("holat") or ""
    qamrov = request.GET.get("qamrov") or "faol"
    tartib = request.GET.get("tartib") or ("balans" if qarz_royxati else "ism")

    # Arxivlanganlar ro'yxatda ko'rinmaydi - ular "Arxiv" bo'limida
    qs = _koradigan_oquvchilar(request.user).filter(arxiv__isnull=True)
    if qarz_royxati:
        qs = _qamrov_filtri(qs, qamrov)
    elif royxat_turi == "chiqarilgan":
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

    qs = balans_bilan(qs)
    if qarz_royxati:
        # Faqat manfiy balansli o'quvchilar + oxirgi to'lov qachon bo'lgani
        qs = qs.filter(balans_summa__lt=0).annotate(
            oxirgi_tolov=Max(
                "tranzaksiyalar__sana",
                filter=Q(tranzaksiyalar__tur=Tranzaksiya.Tur.TOLOV),
            )
        )
    else:
        qs = holat_filtri(qs, holat)

    tartiblar = {
        "ism": ["familiya", "ism"],
        "balans": ["balans_summa"],
        "balans_teskari": ["-balans_summa"],
        "yangi": ["-boshlangan_sana"],
    }
    if qarz_royxati:
        # Eng uzoq to'lamaganlar tepada (umuman to'lamaganlar eng boshida)
        tartiblar["tolov"] = ["oxirgi_tolov", "familiya"]
    qs = qs.order_by(*tartiblar.get(tartib, tartiblar["ism"]))

    sahifalar = Paginator(qs, 50)
    sahifa = sahifalar.get_page(request.GET.get("sahifa"))

    for oquvchi in sahifa:
        oquvchi.holat_info = balans_holati(oquvchi.balans_summa)

    balanslar = list(qs.values_list("balans_summa", flat=True))
    qarzlar = [-b for b in balanslar if b < 0]
    jamlar = {
        "jami": len(balanslar),
        "qarzdor": len(qarzlar),
        "oldindan": sum(1 for b in balanslar if b > 0),
        "qarz_summa": sum(qarzlar) if qarzlar else 0,
        "eng_katta": max(qarzlar) if qarzlar else 0,
    }

    # Yorliqdagi raqam: kursga keladigan qarzdorlar soni (bo'lim filtriga bog'liq emas)
    qarzdorlar_soni = balans_bilan(
        _koradigan_oquvchilar(request.user).filter(faol=True, arxiv__isnull=True)
    ).filter(balans_summa__lt=0).count()

    return render(request, "students/royxat.html", {
        "sahifa": sahifa,
        "guruhlar": request.user.guruhlari.filter(faol=True),
        "jamlar": jamlar,
        "qarz_royxati": qarz_royxati,
        "qarzdorlar_soni": qarzdorlar_soni,
        "filtr": {"q": qidiruv, "guruh": guruh_id, "holat": holat,
                  "royxat": royxat_turi, "tartib": tartib, "qamrov": qamrov},
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


# ------------------------------------------------------------------ arxiv


def _qaytish_manzili(request, standart):
    keyingi = request.POST.get("keyingi") or request.GET.get("keyingi")
    if keyingi and keyingi.startswith("/"):
        return keyingi
    return standart


def oquvchi_arxiv_oyna(request, pk):
    """"Arxivlash" tugmasi ochadigan oynacha."""
    obyekt = get_object_or_404(_koradigan_oquvchilar(request.user), pk=pk)
    keyingi = request.GET.get("keyingi") or ""
    return render(request, "students/_arxiv_oyna.html", {
        "oquvchi": obyekt,
        "form": ArxivForm(),
        "keyingi": keyingi if keyingi.startswith("/") else "",
    })


def oquvchi_arxivlash(request, pk):
    """O'quvchini guruhdan chiqarib arxivga o'tkazadi."""
    obyekt = get_object_or_404(_koradigan_oquvchilar(request.user), pk=pk)
    qaytish = _qaytish_manzili(request, reverse("students:oquvchi", args=[pk]))
    if request.method != "POST":
        return redirect(qaytish)

    if hasattr(obyekt, "arxiv"):
        messages.error(request, f"{obyekt.toliq_ism} allaqachon arxivda.")
        return redirect(qaytish)

    form = ArxivForm(request.POST)
    if not form.is_valid():
        xatolar = "; ".join(" ".join(x) for x in form.errors.values())
        messages.error(request, f"Arxivlanmadi. {xatolar}")
        return redirect(qaytish)

    sana = date.today()
    yozuv = form.save(commit=False)
    yozuv.oquvchi = obyekt
    yozuv.guruh = obyekt.guruh
    yozuv.guruh_nomi = obyekt.guruh.nomi if obyekt.guruh else ""
    yozuv.sana = sana
    yozuv.yaratgan = request.user

    hali_faol = obyekt.faol
    # Guruh olib tashlanadi - shuning uchun narx o'quvchining o'ziga ko'chiriladi,
    # aks holda oxirgi oy hisobi noto'g'ri chiqadi.
    if obyekt.oylik_toluv is None:
        obyekt.oylik_toluv = obyekt.amaldagi_oylik
    obyekt.guruh = None
    obyekt.faol = False
    if hali_faol:
        obyekt.chiqarilgan_sana = sana
    obyekt.chiqarish_sababi = f"Arxiv: {yozuv.get_sabab_display()}"
    obyekt.save()

    if hali_faol:
        # Chiqarilgandagi kabi: keyingi oylar hisobi olib tashlanadi,
        # tugallanmagan oy esa qatnashgan kunlari bo'yicha yopiladi.
        obyekt.tranzaksiyalar.filter(
            tur=Tranzaksiya.Tur.HISOB, davr__gt=oy_boshi(sana)
        ).delete()
        oyni_qayta_hisobla(obyekt, oy_boshi(sana), sana)

    yozuv.save()
    messages.success(
        request,
        f"{obyekt.toliq_ism} arxivga o'tkazildi ({yozuv.get_sabab_display().lower()}).",
    )
    return redirect(qaytish)


def arxiv(request):
    """Arxiv bo'limi: sabab bo'yicha yorliqlarga ajratilgan ro'yxat."""
    asos = Arxiv.objects.all()
    if not request.user.admin_mi:
        asos = asos.filter(guruh__oqituvchi=request.user)

    sanoq = dict(asos.values_list("sabab").annotate(soni=Count("id")))
    bolim = request.GET.get("bolim") or "hammasi"
    qidiruv = (request.GET.get("q") or "").strip()

    qs = asos.select_related("oquvchi", "guruh").annotate(
        balans_summa=balans_ifodasi("oquvchi__tranzaksiyalar")
    ).order_by("-sana", "-id")
    if bolim in Arxiv.Sabab.values:
        qs = qs.filter(sabab=bolim)
    if qidiruv:
        qs = qs.filter(
            Q(oquvchi__ism__icontains=qidiruv) | Q(oquvchi__familiya__icontains=qidiruv)
            | Q(guruh_nomi__icontains=qidiruv)
        )

    sahifalar = Paginator(qs, 50)
    sahifa = sahifalar.get_page(request.GET.get("sahifa"))
    for yozuv in sahifa:
        yozuv.holat_info = balans_holati(yozuv.balans_summa)

    return render(request, "students/arxiv.html", {
        "sahifa": sahifa,
        "bolim": bolim,
        "qidiruv": qidiruv,
        "sanoq": sanoq,
        "jami": sum(sanoq.values()),
        "yorliqlar": [("hammasi", "Hammasi")] + list(Arxiv.Sabab.choices),
    })


def arxivdan_chiqarish(request, pk):
    """Xato arxivlangan o'quvchini arxivdan qaytaradi (ro'yxatga emas)."""
    yozuv = get_object_or_404(Arxiv.objects.select_related("oquvchi", "guruh"), pk=pk)
    if not request.user.admin_mi and (
        yozuv.guruh is None or yozuv.guruh.oqituvchi_id != request.user.pk
    ):
        messages.error(request, "Bu yozuvni faqat admin qaytara oladi.")
        return redirect("students:arxiv")
    if request.method == "POST":
        ism = yozuv.oquvchi.toliq_ism
        yozuv.delete()
        messages.success(
            request,
            f"{ism} arxivdan chiqarildi. U endi \"Chiqarilganlar\" ro'yxatida - "
            f"guruhini tayinlash uchun kartochkasidan ro'yxatga qaytaring.",
        )
    return redirect(_qaytish_manzili(request, reverse("students:arxiv")))


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
