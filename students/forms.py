from datetime import date

from django import forms

from dashboard.widgets import PulInput, SanaInput

from .models import Arxiv, Guruh, Oquvchi


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

    def __init__(self, *args, foydalanuvchi=None, **kwargs):
        super().__init__(*args, **kwargs)
        guruhlar = Guruh.objects.filter(faol=True)
        if foydalanuvchi is not None and not foydalanuvchi.admin_mi:
            # O'qituvchi faqat o'z guruhiga o'quvchi qo'sha oladi
            guruhlar = guruhlar.filter(oqituvchi=foydalanuvchi)
            self.fields["guruh"].required = True
            self.fields["guruh"].empty_label = None
        else:
            self.fields["guruh"].empty_label = "-- Guruhsiz --"
        self.fields["guruh"].queryset = guruhlar
        if self.instance.pk is None:
            self.fields["boshlangan_sana"].initial = date.today()

    def clean(self):
        tozalangan = super().clean()
        # Narx bo'sh qoldirilsa guruhdan olinadi; guruh ham bo'lmasa - narx shart
        if tozalangan.get("oylik_toluv") is None and not tozalangan.get("guruh"):
            self.add_error(
                "oylik_toluv",
                "Guruh tanlanmagan bo'lsa, oylik kurs to'lovini yozing.",
            )
        if not any([tozalangan.get("telefon"), tozalangan.get("ota_telefon"),
                    tozalangan.get("ona_telefon")]):
            self.add_error("telefon", "Kamida bitta telefon raqami kiritilsin.")
        return tozalangan


class GuruhForm(forms.ModelForm):
    class Meta:
        model = Guruh
        fields = ["nomi", "oqituvchi", "oylik_toluv", "faol"]
        widgets = {"oylik_toluv": PulInput()}

    def __init__(self, *args, foydalanuvchi=None, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import Foydalanuvchi

        oqituvchilar = Foydalanuvchi.objects.filter(
            saytga_kira_oladi=True, is_active=True, is_superuser=False,
        )
        if foydalanuvchi is not None and foydalanuvchi.pk:
            # O'zini tanlash uchun bo'sh variant bor - ro'yxatda takrorlanmasin
            oqituvchilar = oqituvchilar.exclude(pk=foydalanuvchi.pk)

        maydon = self.fields["oqituvchi"]
        maydon.queryset = oqituvchilar.order_by("last_name", "first_name")
        maydon.empty_label = "-- O'zim o'qituvchiman --"
        maydon.required = False

        if self.instance.pk is None:
            # Yangi guruhda maydon "0" emas, bo'sh turadi
            self.initial["oylik_toluv"] = None


class ChiqarishForm(forms.Form):
    """O'quvchini kursga keladiganlar ro'yxatidan chiqarish."""

    chiqarilgan_sana = forms.DateField(
        label="Chiqarilgan sana", initial=date.today,
        widget=SanaInput(),
    )
    sabab = forms.CharField(label="Sababi", max_length=200, required=False)


class QaytarishForm(forms.Form):
    """Chiqarilgan o'quvchini ro'yxatga qaytarish."""

    boshlangan_sana = forms.DateField(
        label="Qaytadan kelgan sana", initial=date.today,
        widget=SanaInput(),
        help_text="Shu sanadan yangi hisob boshlanadi.",
    )


class ArxivForm(forms.ModelForm):
    """Arxivlash oynachasi: sabab va unga bog'liq maydonlar."""

    class Meta:
        model = Arxiv
        fields = ["sabab", "biologiya_bali", "jami_ball", "sertifikat"]
        widgets = {
            "sabab": forms.RadioSelect(),
            "biologiya_bali": forms.NumberInput(attrs={"step": "0.1", "min": "0"}),
            "jami_ball": forms.NumberInput(attrs={"step": "0.1", "min": "0"}),
            "sertifikat": forms.TextInput(
                attrs={"placeholder": "Sertifikat raqami yoki darajasi"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # RadioSelect da bo'sh ("---------") variant kerak emas
        self.fields["sabab"].choices = Arxiv.Sabab.choices

    def clean(self):
        """Tanlangan sababga tegishli bo'lmagan maydonlar tozalanadi."""
        tozalangan = super().clean()
        sabab = tozalangan.get("sabab")

        if sabab == Arxiv.Sabab.OQISHGA_KIRDI:
            for nom in ("biologiya_bali", "jami_ball"):
                if tozalangan.get(nom) is None and nom not in self.errors:
                    self.add_error(nom, "Ball kiritilsin.")
            tozalangan["sertifikat"] = ""
        elif sabab == Arxiv.Sabab.SERTIFIKAT:
            if not tozalangan.get("sertifikat"):
                self.add_error("sertifikat", "Sertifikat yozilsin.")
            tozalangan["biologiya_bali"] = None
            tozalangan["jami_ball"] = None
        else:
            tozalangan["sertifikat"] = ""
            tozalangan["biologiya_bali"] = None
            tozalangan["jami_ball"] = None
        return tozalangan
