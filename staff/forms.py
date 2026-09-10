from datetime import date

from django import forms

from accounts.models import Foydalanuvchi
from dashboard.widgets import PulInput, SanaInput
from payments.models import Usul

from .models import Xodim, XodimTranzaksiya

QOLDA_TURLAR = [
    (XodimTranzaksiya.Tur.AVANS, "Avans berish"),
    (XodimTranzaksiya.Tur.OYLIK, "Oylik berish"),
    (XodimTranzaksiya.Tur.BONUS, "Bonus / ustama qo'shish"),
    (XodimTranzaksiya.Tur.JARIMA, "Ushlab qolish"),
]


class XodimForm(forms.ModelForm):
    class Meta:
        model = Xodim
        fields = ["ism", "familiya", "telefon", "oylik_maosh", "izoh"]
        widgets = {
            "oylik_maosh": PulInput(),
            "izoh": forms.Textarea(attrs={"rows": 2}),
            "telefon": forms.TextInput(attrs={"placeholder": "+998 90 123 45 67"}),
        }


class MaoshForm(forms.Form):
    """Oylik maoshni admin tayinlaydi."""

    oylik_maosh = forms.DecimalField(label="Yangi oylik maosh (so'm)", min_value=0,
                                     max_digits=12, decimal_places=2,
                                     widget=PulInput())
    qayta_hisobla = forms.BooleanField(
        label="Shu oyning hisobini yangi maosh bo'yicha qayta hisoblansin",
        required=False, initial=True,
    )


class XodimHisobForm(forms.Form):
    """Xodimga sayt logini berish yoki uni o'zgartirish (faqat admin)."""

    login = forms.CharField(label="Login", max_length=150,
                            widget=forms.TextInput(attrs={"autocomplete": "off"}))
    parol = forms.CharField(
        label="Parol", required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    rol = forms.ChoiceField(label="Huquqi", choices=Foydalanuvchi.Rol.choices,
                            initial=Foydalanuvchi.Rol.OQITUVCHI)

    def __init__(self, *args, hisob=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.hisob = hisob
        if hisob is None:
            self.fields["parol"].required = True
            self.fields["parol"].help_text = "Kamida 4 ta belgi."
        else:
            self.fields["login"].initial = hisob.username
            self.fields["rol"].initial = hisob.rol
            self.fields["parol"].help_text = "Bo'sh qoldirilsa, eski parol o'zgarmaydi."

    def clean_login(self):
        login = self.cleaned_data["login"].strip()
        band = Foydalanuvchi.objects.filter(username=login)
        if self.hisob is not None:
            band = band.exclude(pk=self.hisob.pk)
        if band.exists():
            raise forms.ValidationError("Bu login band. Boshqasini tanlang.")
        return login

    def clean_parol(self):
        parol = self.cleaned_data.get("parol") or ""
        if parol and len(parol) < 4:
            raise forms.ValidationError("Parol kamida 4 ta belgidan iborat bo'lsin.")
        return parol


class HisobBoglashForm(forms.Form):
    """Mavjud sayt hisobini xodimga bog'lash."""

    hisob = forms.ModelChoiceField(
        label="Mavjud hisob", queryset=Foydalanuvchi.objects.none(),
        empty_label="-- hisobni tanlang --",
    )

    def __init__(self, *args, joriy_foydalanuvchi=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Foydalanuvchi.objects.filter(is_superuser=False, xodim__isnull=True)
        if joriy_foydalanuvchi is not None:
            # O'zini xodim qilib qo'ya olmaydi
            qs = qs.exclude(pk=joriy_foydalanuvchi.pk)
        self.fields["hisob"].queryset = qs.order_by("username")


class TezOylikForm(forms.Form):
    """Xodimlar ro'yxatidagi "To'lov" tugmasi uchun sodda forma.

    Uchta narsa: avansmi yoki oylikmi, naqdmi yoki plastikmi, va qancha.
    """

    tur = forms.ChoiceField(
        label="Amal turi",
        choices=[(XodimTranzaksiya.Tur.AVANS, "Avans"),
                 (XodimTranzaksiya.Tur.OYLIK, "Oylik")],
        widget=forms.RadioSelect, initial=XodimTranzaksiya.Tur.AVANS,
    )
    usul = forms.ChoiceField(label="To'lov usuli", choices=Usul.choices,
                             widget=forms.RadioSelect, initial=Usul.NAQD)
    summa = forms.DecimalField(
        label="Summa (so'm)", max_digits=12, decimal_places=2,
        widget=PulInput(attrs={"placeholder": "0", "autofocus": True}),
    )

    def clean_summa(self):
        summa = self.cleaned_data["summa"]
        if summa <= 0:
            raise forms.ValidationError("Summa noldan katta bo'lsin.")
        return summa
