from datetime import date

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class Guruh(models.Model):
    nomi = models.CharField("Guruh nomi", max_length=100, unique=True)
    oylik_toluv = models.DecimalField(
        "Oylik kurs to'lovi (so'm)", max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        help_text="Yangi o'quvchi qo'shilganda shu summa avtomatik qo'yiladi.",
    )
    faol = models.BooleanField("Faol", default=True)
    yaratilgan = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Guruh"
        verbose_name_plural = "Guruhlar"
        ordering = ["nomi"]

    def __str__(self):
        return self.nomi

    @property
    def faol_oquvchilar_soni(self):
        return self.oquvchilar.filter(faol=True).count()


class OquvchiQuerySet(models.QuerySet):
    def faol(self):
        return self.filter(faol=True)

    def chiqarilgan(self):
        return self.filter(faol=False)


class Oquvchi(models.Model):
    """Kursga qatnaydigan o'quvchi."""

    ism = models.CharField("Ism", max_length=60)
    familiya = models.CharField("Familiya", max_length=60)

    telefon = models.CharField("O'quvchi telefoni", max_length=30, blank=True)
    ota_telefon = models.CharField("Ota telefoni", max_length=30, blank=True)
    ona_telefon = models.CharField("Ona telefoni", max_length=30, blank=True)

    guruh = models.ForeignKey(Guruh, verbose_name="Guruh", on_delete=models.SET_NULL,
                              null=True, blank=True, related_name="oquvchilar")

    oylik_toluv = models.DecimalField(
        "Oylik kurs to'lovi (so'm)", max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        help_text="Bir oylik to'liq narx. Kunlik narx = shu summa / oydagi kunlar soni.",
    )

    boshlangan_sana = models.DateField(
        "Kursga kelgan sana", default=date.today,
        help_text="Birinchi oy shu sanadan keyingi oyning 1-sanasigacha kunlab hisoblanadi.",
    )

    faol = models.BooleanField("Ro'yxatda (kursga keladi)", default=True)
    chiqarilgan_sana = models.DateField("Kursdan chiqarilgan sana", null=True, blank=True)
    chiqarish_sababi = models.CharField("Chiqarish sababi", max_length=200, blank=True)

    izoh = models.TextField("Izoh", blank=True)
    yaratilgan = models.DateTimeField(auto_now_add=True)
    yangilangan = models.DateTimeField(auto_now=True)

    objects = OquvchiQuerySet.as_manager()

    class Meta:
        verbose_name = "O'quvchi"
        verbose_name_plural = "O'quvchilar"
        ordering = ["familiya", "ism"]
        indexes = [models.Index(fields=["faol"]), models.Index(fields=["familiya", "ism"])]

    def __str__(self):
        return self.toliq_ism

    def get_absolute_url(self):
        return reverse("students:oquvchi", args=[self.pk])

    def save(self, *args, **kwargs):
        if self.faol:
            self.chiqarilgan_sana = None
        elif self.chiqarilgan_sana is None:
            self.chiqarilgan_sana = date.today()
        super().save(*args, **kwargs)

    @property
    def toliq_ism(self):
        return f"{self.familiya} {self.ism}".strip()

    @property
    def bosh_harflar(self):
        return f"{self.familiya[:1]}{self.ism[:1]}".upper()

    @property
    def telefonlar(self):
        """Kiritilgan barcha raqamlar ro'yxati: (yorliq, raqam)."""
        return [(y, r) for y, r in (
            ("O'quvchi", self.telefon),
            ("Ota", self.ota_telefon),
            ("Ona", self.ona_telefon),
        ) if r]

    # --- Moliyaviy holat (payments ilovasi hisoblaydi) ---

    @property
    def balans(self):
        """Musbat = oldindan to'langan, manfiy = qarzdor."""
        from payments.services import oquvchi_balansi
        return oquvchi_balansi(self)

    @property
    def holat(self):
        from payments.services import balans_holati
        return balans_holati(self.balans)
