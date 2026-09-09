from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

class SaytKirishForm(AuthenticationForm):
    """Sayt panelining kirish formasi (Django admin formasidan alohida)."""

    username = forms.CharField(
        label="Login",
        widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "Loginingiz",
                                      "autocomplete": "username"}),
    )
    password = forms.CharField(
        label="Parol",
        widget=forms.PasswordInput(attrs={"placeholder": "Parolingiz",
                                          "autocomplete": "current-password"}),
    )

    error_messages = {
        "invalid_login": "Login yoki parol noto'g'ri.",
        "inactive": "Bu hisob o'chirilgan.",
    }

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.saytga_kira_oladi:
            # Django admin uchun ochilgan texnik superuser hisoblari sayt paneliga
            # kira olmaydi - ikkala panel bir-biridan mustaqil.
            raise ValidationError(
                "Bu hisob sayt paneliga kira olmaydi. Sayt uchun alohida login bering.",
                code="taqiq",
            )
