from datetime import date

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from students.models import Oquvchi


class Usul(models.TextChoices):
    NAQD = "naqd", "Naqd pul"
    PLASTIK = "plastik", "Plastik karta"


class Karta(models.Model):
    """To'lov qabul qilinadigan plastik kartalar (o'qituvchi/markaz kartalari)."""

    nomi = models.CharField("Karta nomi", max_length=80, help_text="Masalan: Humo - asosiy")
    raqam = models.CharField("Karta raqami", max_length=30)
    egasi = models.CharField("Karta egasi", max_length=80, blank=True)
    faol = models.BooleanField("Faol", default=True)

    class Meta:
        verbose_name = "Karta"
        verbose_name_plural = "Kartalar"
        ordering = ["-faol", "nomi"]

    def __str__(self):
        return f"{self.nomi} ({self.raqam})"


class TranzaksiyaQuerySet(models.QuerySet):
    def tolovlar(self):
        return self.filter(tur=Tranzaksiya.Tur.TOLOV)

    def davr_ichida(self, boshi=None, oxiri=None):
        natija = self
        if boshi:
            natija = natija.filter(sana__gte=boshi)
        if oxiri:
            natija = natija.filter(sana__lte=oxiri)
        return natija


class Tranzaksiya(models.Model):
    """O'quvchining moliyaviy harakati (hisoblangan pul yoki to'lov).

    Balans = barcha tranzaksiyalarning ishorali summasi.
      musbat balans -> oldindan to'langan
      manfiy balans -> qarzdor
    """

    class Tur(models.TextChoices):
        HISOB = "hisob", "Hisoblangan kurs to'lovi"
        TOLOV = "tolov", "To'lov qabul qilindi"
        CHEGIRMA = "chegirma", "Chegirma"
        QAYTARISH = "qaytarish", "Pul qaytarildi"
        QARZ = "qarz", "O'qituvchi qarzi (oldindan to'lovga o'tdi)"

    # Balansga qanday ta'sir qiladi: +1 o'quvchi foydasiga, -1 o'quvchi zimmasiga
    ISHORA = {
        Tur.HISOB: -1,
        Tur.TOLOV: +1,
        Tur.CHEGIRMA: +1,
        Tur.QAYTARISH: -1,
        Tur.QARZ: +1,
    }

    oquvchi = models.ForeignKey(Oquvchi, verbose_name="O'quvchi", on_delete=models.CASCADE,
                                related_name="tranzaksiyalar")
    tur = models.CharField("Turi", max_length=20, choices=Tur.choices)
    summa = models.DecimalField("Summa (so'm)", max_digits=12, decimal_places=2,
                                validators=[MinValueValidator(0)])
    sana = models.DateField("Sana", default=date.today)

    usul = models.CharField("To'lov usuli", max_length=10, choices=Usul.choices, blank=True)
    karta = models.ForeignKey(Karta, verbose_name="Karta", on_delete=models.SET_NULL,
                              null=True, blank=True, related_name="tranzaksiyalar")
    karta_raqami = models.CharField("Karta raqami", max_length=30, blank=True)

    davr = models.DateField("Hisob davri (oy boshi)", null=True, blank=True,
                            help_text="Faqat hisoblangan kurs to'lovlari uchun.")
    kunlar = models.PositiveSmallIntegerField("Hisoblangan kunlar", null=True, blank=True)

    izoh = models.CharField("Izoh", max_length=255, blank=True)
    yaratgan = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Kiritdi",
                                 on_delete=models.SET_NULL, null=True, blank=True)
    yaratilgan = models.DateTimeField(auto_now_add=True)

    objects = TranzaksiyaQuerySet.as_manager()

    class Meta:
        verbose_name = "Tranzaksiya"
        verbose_name_plural = "Tranzaksiyalar"
        ordering = ["-sana", "-id"]
        indexes = [
            models.Index(fields=["tur", "sana"]),
            models.Index(fields=["oquvchi", "sana"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["oquvchi", "davr"],
                condition=models.Q(tur="hisob"),
                name="bir_oyga_bitta_hisob",
            )
        ]

    def __str__(self):
        return f"{self.oquvchi} - {self.get_tur_display()} - {self.summa}"

    @property
    def ishorali_summa(self):
        return self.summa * self.ISHORA.get(self.tur, 0)

    @property
    def kirim_mi(self):
        """Kassaga haqiqiy pul tushganmi (statistikada kirim sifatida hisoblanadi)."""
        return self.tur == self.Tur.TOLOV

    @property
    def karta_korinishi(self):
        return self.karta_raqami or (self.karta.raqam if self.karta else "")
