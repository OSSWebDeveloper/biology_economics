from datetime import date

from django import forms

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
        fields = ["ism", "familiya", "lavozim", "telefon", "karta_raqami",
                  "oylik_maosh", "ishga_kirgan_sana", "izoh"]
        widgets = {
            "ishga_kirgan_sana": SanaInput(),
            "oylik_maosh": PulInput(),
            "izoh": forms.Textarea(attrs={"rows": 2}),
            "telefon": forms.TextInput(attrs={"placeholder": "+998 90 123 45 67"}),
            "karta_raqami": forms.TextInput(attrs={"placeholder": "8600 **** **** 1234"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk is None:
            self.fields["ishga_kirgan_sana"].initial = date.today()


class XodimTolovForm(forms.ModelForm):
    """Xodimga avans / oylik berish formasi."""

    tur = forms.ChoiceField(label="Amal turi", choices=QOLDA_TURLAR,
                            initial=XodimTranzaksiya.Tur.AVANS)

    class Meta:
        model = XodimTranzaksiya
        fields = ["tur", "summa", "sana", "usul", "karta_raqami", "izoh"]
        widgets = {
            "sana": SanaInput(),
            "summa": PulInput(),
            "karta_raqami": forms.TextInput(attrs={"placeholder": "8600 **** **** 1234"}),
            "izoh": forms.TextInput(attrs={"placeholder": "Ixtiyoriy izoh"}),
        }

    def __init__(self, *args, xodim=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sana"].initial = date.today()
        self.fields["usul"].required = False
        if xodim is not None and not self.is_bound:
            self.fields["karta_raqami"].initial = xodim.karta_raqami

    def clean(self):
        tozalangan = super().clean()
        tur = tozalangan.get("tur")
        usul = tozalangan.get("usul")
        summa = tozalangan.get("summa")

        if summa is not None and summa <= 0:
            self.add_error("summa", "Summa noldan katta bo'lsin.")

        pul_harakati = tur in (XodimTranzaksiya.Tur.AVANS, XodimTranzaksiya.Tur.OYLIK)
        if pul_harakati and not usul:
            self.add_error("usul", "To'lov usulini tanlang (naqd yoki plastik).")
        if not pul_harakati:
            tozalangan["usul"] = ""
            tozalangan["karta_raqami"] = ""
        if usul == Usul.PLASTIK and pul_harakati and not tozalangan.get("karta_raqami"):
            self.add_error("karta_raqami", "Plastik uchun karta raqamini yozing.")
        return tozalangan


class MaoshForm(forms.Form):
    """Oylik maoshni admin tayinlaydi."""

    oylik_maosh = forms.DecimalField(label="Yangi oylik maosh (so'm)", min_value=0,
                                     max_digits=12, decimal_places=2,
                                     widget=PulInput())
    qayta_hisobla = forms.BooleanField(
        label="Shu oyning hisobini yangi maosh bo'yicha qayta hisoblansin",
        required=False, initial=True,
    )
