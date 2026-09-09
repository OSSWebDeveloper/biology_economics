from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .forms import FoydalanuvchiForm, ParolForm, SaytKirishForm, ShaxsiyForm
from .models import Foydalanuvchi
from .permissions import admin_talab


class SaytKirish(auth_views.LoginView):
    """Sayt panelining kirish sahifasi (/kirish/).

    Django admin kirish sahifasi (/boshqaruv/login/) bundan mustaqil ishlaydi.
    """

    template_name = "accounts/kirish.html"
    authentication_form = SaytKirishForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        javob = super().form_valid(form)
        messages.success(self.request, f"Xush kelibsiz, {self.request.user.toliq_ism}!")
        return javob


class SaytChiqish(auth_views.LogoutView):
    next_page = reverse_lazy("accounts:kirish")


def shaxsiy(request):
    """Shaxsiy sahifam: o'z ismi, logini va parolini o'zgartirish.

    Admin uchun bu sahifada barcha foydalanuvchilar ro'yxati ham ko'rinadi.
    """
    amal = request.POST.get("amal", "")

    malumot_form = ShaxsiyForm(
        request.POST if amal == "malumot" else None, instance=request.user)
    parol_form = ParolForm(
        request.user, request.POST if amal == "parol" else None)

    if request.method == "POST":
        if amal == "malumot" and malumot_form.is_valid():
            malumot_form.save()
            messages.success(request, "Ma'lumotlaringiz saqlandi.")
            return redirect("accounts:shaxsiy")
        if amal == "parol" and parol_form.is_valid():
            parol_form.save()
            update_session_auth_hash(request, request.user)   # sessiya uzilmasin
            messages.success(request, "Parol o'zgartirildi.")
            return redirect("accounts:shaxsiy")
        messages.error(request, "Saqlanmadi - maydonlarni tekshiring.")

    boshqalar = None
    if request.user.admin_mi:
        # Django admin uchun ochilgan texnik superuser hisoblari bu ro'yxatda
        # ko'rinmaydi - ikkala panel bir-biridan mustaqil bo'lib qolsin.
        boshqalar = (Foydalanuvchi.objects.exclude(pk=request.user.pk)
                     .exclude(is_superuser=True).order_by("username"))

    return render(request, "accounts/shaxsiy.html", {
        "malumot_form": malumot_form,
        "parol_form": parol_form,
        "boshqalar": boshqalar,
    })


@admin_talab
def foydalanuvchi_saqlash(request, pk=None):
    """Admin boshqa foydalanuvchini yaratadi yoki tahrirlaydi."""
    obyekt = get_object_or_404(Foydalanuvchi, pk=pk) if pk else None
    if obyekt is not None and obyekt == request.user:
        messages.info(request, "O'z ma'lumotlaringizni shu sahifadan o'zgartirasiz.")
        return redirect("accounts:shaxsiy")
    if obyekt is not None and obyekt.is_superuser and not request.user.is_superuser:
        messages.error(request, "Texnik Django admin hisobini bu yerdan o'zgartirib bo'lmaydi.")
        return redirect("accounts:shaxsiy")

    form = FoydalanuvchiForm(request.POST or None, instance=obyekt)
    if request.method == "POST" and form.is_valid():
        yangi = form.save()
        messages.success(request, f"{yangi.toliq_ism} saqlandi.")
        return redirect("accounts:shaxsiy")

    return render(request, "accounts/foydalanuvchi_form.html", {
        "form": form,
        "obyekt": obyekt,
        "sarlavha": (f"{obyekt.toliq_ism} - ma'lumotlarini o'zgartirish"
                     if obyekt else "Yangi foydalanuvchi"),
    })


@admin_talab
def foydalanuvchi_ochirish(request, pk):
    obyekt = get_object_or_404(Foydalanuvchi, pk=pk)
    if obyekt == request.user:
        messages.error(request, "O'zingizni o'chira olmaysiz.")
    elif obyekt.is_superuser and not request.user.is_superuser:
        messages.error(request, "Texnik Django admin hisobini o'chirib bo'lmaydi.")
    elif request.method == "POST":
        ism = obyekt.toliq_ism
        try:
            obyekt.delete()
            messages.success(request, f"{ism} o'chirildi.")
        except ProtectedError:
            obyekt.saytga_kira_oladi = False
            obyekt.is_active = False
            obyekt.save(update_fields=["saytga_kira_oladi", "is_active"])
            messages.warning(request, f"{ism}ga bog'liq yozuvlar bor - o'rniga bloklandi.")
    return redirect("accounts:shaxsiy")
