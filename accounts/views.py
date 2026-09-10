from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import ParolForm, SaytKirishForm, ShaxsiyForm


class SaytKirish(auth_views.LoginView):
    """Sayt panelining kirish sahifasi (/kirish/).

    Django admin kirish sahifasi (/boshqaruv/login/) bundan mustaqil ishlaydi.
    """

    template_name = "accounts/kirish.html"
    authentication_form = SaytKirishForm
    redirect_authenticated_user = True


class SaytChiqish(auth_views.LogoutView):
    next_page = reverse_lazy("accounts:kirish")


def shaxsiy(request):
    """Shaxsiy sahifam: o'z ismi, logini va parolini o'zgartirish.

    Boshqa xodimlarning logini va paroli ularning o'z kartochkasidan
    (Xodimlar bo'limi) boshqariladi - bu yerda faqat o'zingiz.
    """
    amal = request.POST.get("amal", "")

    malumot_form = ShaxsiyForm(
        request.POST if amal == "malumot" else None, instance=request.user)
    parol_form = ParolForm(
        request.user, request.POST if amal == "parol" else None)

    if request.method == "POST":
        if amal == "malumot" and malumot_form.is_valid():
            malumot_form.save()
            _ismni_xodimga_kochir(request.user)
            messages.success(request, "Ma'lumotlaringiz saqlandi.")
            return redirect("accounts:shaxsiy")
        if amal == "parol" and parol_form.is_valid():
            parol_form.save()
            update_session_auth_hash(request, request.user)   # sessiya uzilmasin
            messages.success(request, "Parol o'zgartirildi.")
            return redirect("accounts:shaxsiy")
        messages.error(request, "Saqlanmadi - maydonlarni tekshiring.")

    return render(request, "accounts/shaxsiy.html", {
        "malumot_form": malumot_form,
        "parol_form": parol_form,
    })


def _ismni_xodimga_kochir(foydalanuvchi):
    """Hisob ismi o'zgarsa, unga bog'langan xodim kartochkasi ham yangilanadi."""
    xodim = getattr(foydalanuvchi, "xodim", None)
    if xodim is None:
        return
    xodim.ism = foydalanuvchi.first_name
    xodim.familiya = foydalanuvchi.last_name
    xodim.telefon = foydalanuvchi.telefon
    xodim.save(update_fields=["ism", "familiya", "telefon"])
