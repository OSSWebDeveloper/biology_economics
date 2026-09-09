from datetime import date

from django import forms

from dashboard.widgets import PulInput, SanaInput

from .models import Guruh, Oquvchi


class OquvchiForm(forms.ModelForm):
    class Meta:
        model = Oquvchi
        fields = ["ism", "familiya", "telefon", "ota_telefon", "ona_telefon",
                  "guruh", "oylik_toluv", "boshlangan_sana", "izoh"]
        widgets = {
            "boshlangan_sana": SanaInput(),
            "oylik_toluv": PulInput(),
            "izoh": forms.Textarea(attrs={"rows": 2}),
            "telefon": forms.TextInput(attrs={"placeholder": "+998 90 123 45 67"}),
            "ota_telefon": forms.TextInput(attrs={"placeholder": "+998 90 123 45 67"}),
            "ona_telefon": forms.TextInput(attrs={"placeholder": "+998 90 123 45 67"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["guruh"].queryset = Guruh.objects.filter(faol=True)
        self.fields["guruh"].empty_label = "-- Guruhsiz --"
        if self.instance.pk is None:
            self.fields["boshlangan_sana"].initial = date.today()

    def clean(self):
        tozalangan = super().clean()
        if not tozalangan.get("oylik_toluv") and tozalangan.get("guruh"):
            tozalangan["oylik_toluv"] = tozalangan["guruh"].oylik_toluv
        if not any([tozalangan.get("telefon"), tozalangan.get("ota_telefon"),
                    tozalangan.get("ona_telefon")]):
            self.add_error("telefon", "Kamida bitta telefon raqami kiritilsin.")
        return tozalangan


class GuruhForm(forms.ModelForm):
    class Meta:
        model = Guruh
        fields = ["nomi", "oylik_toluv", "faol"]
        widgets = {"oylik_toluv": PulInput()}


class ChiqarishForm(forms.Form):
    """O'quvchini kursga keladiganlar ro'yxatidan chiqarish."""

    chiqarilgan_sana = forms.DateField(
        label="Chiqarilgan sana", initial=date.today,
        widget=SanaInput(),
    )
    sabab = forms.CharField(label="Sababi", max_length=200, required=False)
    qayta_hisobla = forms.BooleanField(
        label="Oxirgi oyni kunlarga bo'lib qayta hisoblansin", required=False, initial=True,
        help_text="Chiqarilgan sanagacha bo'lgan kunlar uchungina pul hisoblanadi.",
    )


class QaytarishForm(forms.Form):
    """Chiqarilgan o'quvchini ro'yxatga qaytarish."""

    boshlangan_sana = forms.DateField(
        label="Qaytadan kelgan sana", initial=date.today,
        widget=SanaInput(),
        help_text="Shu sanadan yangi hisob boshlanadi.",
    )
