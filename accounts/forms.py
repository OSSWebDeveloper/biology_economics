from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError

from .models import Foydalanuvchi


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


class ShaxsiyForm(forms.ModelForm):
    """Foydalanuvchi o'z ismi va loginini o'zgartiradi."""

    class Meta:
        model = Foydalanuvchi
        fields = ["last_name", "first_name", "telefon", "username"]
        labels = {
            "last_name": "Familiya",
            "first_name": "Ism",
            "username": "Login",
        }
        help_texts = {
            "username": "Saytga kirishda shu nom yoziladi.",
        }
        widgets = {
            "telefon": forms.TextInput(attrs={"placeholder": "+998 90 123 45 67"}),
        }


class ParolForm(PasswordChangeForm):
    """O'z parolini almashtirish - eski parolni so'raydi."""

    old_password = forms.CharField(
        label="Joriy parol",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    new_password1 = forms.CharField(
        label="Yangi parol",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Kamida 4 ta belgi.",
    )
    new_password2 = forms.CharField(
        label="Yangi parolni takrorlang",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    error_messages = {
        "password_incorrect": "Joriy parol noto'g'ri.",
        "password_mismatch": "Yangi parollar mos kelmadi.",
    }


class FoydalanuvchiForm(forms.ModelForm):
    """Admin boshqa foydalanuvchini yaratadi yoki tahrirlaydi."""

    parol1 = forms.CharField(
        label="Parol", required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    parol2 = forms.CharField(
        label="Parolni takrorlang", required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = Foydalanuvchi
        fields = ["last_name", "first_name", "telefon", "username", "rol",
                  "saytga_kira_oladi"]
        labels = {
            "last_name": "Familiya",
            "first_name": "Ism",
            "username": "Login",
        }
        widgets = {
            "telefon": forms.TextInput(attrs={"placeholder": "+998 90 123 45 67"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk is None:
            self.fields["parol1"].required = True
            self.fields["parol2"].required = True
            self.fields["parol1"].help_text = "Kamida 4 ta belgi."
        else:
            self.fields["parol1"].help_text = (
                "Bo'sh qoldirilsa, eski parol o'zgarmaydi.")

    def clean(self):
        tozalangan = super().clean()
        p1, p2 = tozalangan.get("parol1"), tozalangan.get("parol2")
        if p1 or p2:
            if p1 != p2:
                self.add_error("parol2", "Parollar mos kelmadi.")
            elif len(p1) < 4:
                self.add_error("parol1", "Parol kamida 4 ta belgidan iborat bo'lsin.")
        return tozalangan

    def save(self, commit=True):
        obyekt = super().save(commit=False)
        parol = self.cleaned_data.get("parol1")
        if parol:
            obyekt.set_password(parol)
        if commit:
            obyekt.save()
        return obyekt
