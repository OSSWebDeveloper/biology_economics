from datetime import date

from django import forms

from dashboard.widgets import PulInput, SanaInput

from .models import Tranzaksiya, Usul

# Qo'lda kiritish mumkin bo'lgan turlar (hisob avtomatik ochiladi)
QOLDA_TURLAR = [
    (Tranzaksiya.Tur.TOLOV, "To'lov qabul qilish"),
    (Tranzaksiya.Tur.CHEGIRMA, "Chegirma berish"),
    (Tranzaksiya.Tur.QARZ, "O'qituvchi qarzi (oldindan to'lovga qo'shiladi)"),
    (Tranzaksiya.Tur.QAYTARISH, "Pulni qaytarib berish"),
]


class TolovForm(forms.ModelForm):
    """O'quvchi kartochkasidagi oynachada ochiladigan to'lov formasi."""

    tur = forms.ChoiceField(label="Amal turi", choices=QOLDA_TURLAR,
                            initial=Tranzaksiya.Tur.TOLOV)

    class Meta:
        model = Tranzaksiya
        fields = ["tur", "summa", "sana", "usul", "izoh"]
        widgets = {
            "sana": SanaInput(),
            "summa": PulInput(attrs={"placeholder": "0"}),
            "izoh": forms.TextInput(attrs={"placeholder": "Ixtiyoriy izoh"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sana"].initial = date.today()
        self.fields["usul"].required = False

    def clean(self):
        tozalangan = super().clean()
        tur = tozalangan.get("tur")
        usul = tozalangan.get("usul")
        summa = tozalangan.get("summa")

        if summa is not None and summa <= 0:
            self.add_error("summa", "Summa noldan katta bo'lsin.")

        pul_harakati = tur in (Tranzaksiya.Tur.TOLOV, Tranzaksiya.Tur.QAYTARISH)
        if pul_harakati and not usul:
            self.add_error("usul", "To'lov usulini tanlang (naqd yoki plastik).")
        if not pul_harakati:
            tozalangan["usul"] = ""
        return tozalangan


class TolovFiltrForm(forms.Form):
    """To'lovlar ro'yxati uchun filtr."""

    USUL_TANLOV = [("", "Barcha usullar")] + list(Usul.choices)

    q = forms.CharField(label="Qidiruv", required=False,
                        widget=forms.TextInput(attrs={"placeholder": "Ism, familiya yoki telefon"}))
    usul = forms.ChoiceField(label="To'lov usuli", choices=USUL_TANLOV, required=False)
    sanadan = forms.DateField(label="Sanadan", required=False,
                              widget=SanaInput())
    sanagacha = forms.DateField(label="Sanagacha", required=False,
                                widget=SanaInput())


class TezTolovForm(forms.Form):
    """Ro'yxatdagi "To'lov" tugmasi uchun eng sodda forma.

    Faqat ikki narsa so'raladi: naqdmi yoki plastikmi, va qancha.
    """

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
