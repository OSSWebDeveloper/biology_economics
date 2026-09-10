from datetime import date

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.permissions import admin_talab
from students.models import Oquvchi

from .forms import KartaForm, TezTolovForm, TolovFiltrForm, TolovForm
from .models import Karta, Tranzaksiya, Usul


def _qaytish_manzili(request, standart):
    keyingi = request.POST.get("keyingi") or request.GET.get("keyingi")
    if keyingi and keyingi.startswith("/"):
        return keyingi
    return standart


def tolovlar(request):
    """Barcha moliyaviy amallar ro'yxati + filtr."""
    filtr = TolovFiltrForm(request.GET or None)
    qs = Tranzaksiya.objects.select_related("oquvchi", "karta", "yaratgan")

    if filtr.is_valid():
        m = filtr.cleaned_data
        if m.get("q"):
            qs = qs.filter(
                Q(oquvchi__ism__icontains=m["q"]) | Q(oquvchi__familiya__icontains=m["q"])
                | Q(oquvchi__telefon__icontains=m["q"])
            )
        if m.get("tur"):
            qs = qs.filter(tur=m["tur"])
        if m.get("usul"):
            qs = qs.filter(usul=m["usul"])
        if m.get("karta"):
            qs = qs.filter(karta=m["karta"])
        if m.get("sanadan"):
            qs = qs.filter(sana__gte=m["sanadan"])
        if m.get("sanagacha"):
            qs = qs.filter(sana__lte=m["sanagacha"])

    tolovlar_qs = qs.filter(tur=Tranzaksiya.Tur.TOLOV)
    jamlar = {
        "jami_tolov": tolovlar_qs.aggregate(s=Sum("summa"))["s"] or 0,
        "naqd": tolovlar_qs.filter(usul=Usul.NAQD).aggregate(s=Sum("summa"))["s"] or 0,
        "plastik": tolovlar_qs.filter(usul=Usul.PLASTIK).aggregate(s=Sum("summa"))["s"] or 0,
        "soni": qs.count(),
    }

    sahifalar = Paginator(qs, 60)
    return render(request, "payments/royxat.html", {
        "sahifa": sahifalar.get_page(request.GET.get("sahifa")),
        "filtr": filtr,
        "jamlar": jamlar,
    })


def tolov_qoshish(request, oquvchi_id):
    """Oynachadagi to'lov formasini qabul qiladi."""
    oquvchi = get_object_or_404(Oquvchi, pk=oquvchi_id)
    qaytish = _qaytish_manzili(request, reverse("students:oquvchi", args=[oquvchi.pk]))

    if request.method != "POST":
        return redirect(qaytish)

    form = TolovForm(request.POST)
    if form.is_valid():
        tranzaksiya = form.save(commit=False)
        tranzaksiya.oquvchi = oquvchi
        tranzaksiya.yaratgan = request.user
        tranzaksiya.save()
        messages.success(
            request,
            f"{oquvchi.toliq_ism}: {tranzaksiya.get_tur_display().lower()} - "
            f"{tranzaksiya.summa:,.0f} so'm saqlandi.".replace(",", " "),
        )
    else:
        xatolar = "; ".join(
            f"{form.fields[m].label if m in form.fields else m}: {' '.join(x)}"
            for m, x in form.errors.items()
        )
        messages.error(request, f"Saqlanmadi. {xatolar}")
    return redirect(qaytish)


def tez_tolov_oyna(request, oquvchi_id):
    """Ro'yxatdagi "To'lov" tugmasi ochadigan sodda oynacha."""
    oquvchi = get_object_or_404(Oquvchi, pk=oquvchi_id)
    keyingi = request.GET.get("keyingi") or ""
    return render(request, "payments/_tez_tolov.html", {
        "oquvchi": oquvchi,
        "balans": oquvchi.balans,
        "form": TezTolovForm(),
        "keyingi": keyingi if keyingi.startswith("/") else "",
    })


def tez_tolov(request, oquvchi_id):
    """Sodda oynachadan kelgan to'lovni saqlaydi."""
    oquvchi = get_object_or_404(Oquvchi, pk=oquvchi_id)
    qaytish = _qaytish_manzili(request, reverse("students:oquvchilar"))
    if request.method != "POST":
        return redirect(qaytish)

    form = TezTolovForm(request.POST)
    if form.is_valid():
        Tranzaksiya.objects.create(
            oquvchi=oquvchi,
            tur=Tranzaksiya.Tur.TOLOV,
            summa=form.cleaned_data["summa"],
            sana=date.today(),
            usul=form.cleaned_data["usul"],
            yaratgan=request.user,
        )
        messages.success(
            request,
            f"{oquvchi.toliq_ism}: {form.cleaned_data['summa']:,.0f} so'm "
            f"qabul qilindi.".replace(",", " "),
        )
    else:
        xatolar = "; ".join(" ".join(x) for x in form.errors.values())
        messages.error(request, f"Saqlanmadi. {xatolar}")
    return redirect(qaytish)


@admin_talab
def tolov_ochirish(request, pk):
    tranzaksiya = get_object_or_404(Tranzaksiya, pk=pk)
    qaytish = _qaytish_manzili(
        request, reverse("students:oquvchi", args=[tranzaksiya.oquvchi_id])
    )
    if request.method == "POST":
        if tranzaksiya.tur == Tranzaksiya.Tur.HISOB:
            messages.error(request, "Avtomatik hisoblangan yozuvni o'chirib bo'lmaydi.")
        else:
            tranzaksiya.delete()
            messages.success(request, "Yozuv o'chirildi.")
    return redirect(qaytish)


# ------------------------------------------------------------------ kartalar

@admin_talab
def kartalar(request):
    return render(request, "payments/kartalar.html", {"royxat": Karta.objects.all()})


@admin_talab
def karta_saqlash(request, pk=None):
    obyekt = get_object_or_404(Karta, pk=pk) if pk else None
    form = KartaForm(request.POST or None, instance=obyekt)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Karta saqlandi.")
        return redirect("payments:kartalar")
    return render(request, "payments/karta_form.html", {
        "form": form,
        "sarlavha": "Kartani tahrirlash" if obyekt else "Yangi karta",
    })


@admin_talab
def karta_ochirish(request, pk):
    obyekt = get_object_or_404(Karta, pk=pk)
    if request.method == "POST":
        obyekt.faol = False
        obyekt.save(update_fields=["faol"])
        messages.success(request, "Karta arxivlandi.")
    return redirect("payments:kartalar")
