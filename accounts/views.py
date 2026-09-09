from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from .forms import SaytKirishForm


class SaytKirish(auth_views.LoginView):
    """Sayt panelining kirish sahifasi (/kirish/).

    Django admin kirish sahifasi (/boshqaruv/login/) bundan mustaqil ishlaydi.
    Foydalanuvchi hisoblari Django admin yoki `manage.py sayt_admin` orqali
    boshqariladi - sayt panelida alohida bo'lim yo'q.
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
