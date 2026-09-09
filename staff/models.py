from datetime import date

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from payments.models import Usul


class Xodim(models.Model):
    """Kurs xodimi. Oyligini faqat admin tayinlaydi."""

    ism = models.CharField("Ism", max_length=60)
    familiya = models.CharField("Familiya", max_length=60)
    lavozim = models.CharField("Lavozim", max_length=80, blank=True,
                               help_text="Masalan: o'qituvchi, administrator, farrosh")
    telefon = models.CharField("Telefon", max_length=30, blank=True)
    karta_raqami = models.CharField("Plastik karta raqami", max_length=30, blank=True,
                                    help_text="Oylik plastikka o'tkazilganda ishlatiladi.")

    oylik_maosh = models.DecimalField(
        "Oylik maosh (so'm)", max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        help_text="Har oyning 1-sanasida shu summa avtomatik hisoblanadi.",
    )

    ishga_kirgan_sana = models.DateField("Ishga kirgan sana", default=date.today)
    faol = models.BooleanField("Ishlayapti", default=True)
    ishdan_ketgan_sana = models.DateField("Ishdan ketgan sana", null=True, blank=True)

    foydalanuvchi = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name="Sayt hisobi",
        on_delete=models.SET_NULL, null=True, blank=True, related_name="xodim",
        help_text="Xodim saytga kirishi kerak bo'lsa, unga login beriladi.",
    )

    izoh = models.TextField("Izoh", blank=True)
    yaratilgan = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Xodim"
        verbose_name_plural = "Xodimlar"
        ordering = ["familiya", "ism"]

    def __str__(self):
        return self.toliq_ism

    def get_absolute_url(self):
        return reverse("staff:xodim", args=[self.pk])

    def save(self, *args, **kwargs):
        if self.faol:
            self.ishdan_ketgan_sana = None
        elif self.ishdan_ketgan_sana is None:
            self.ishdan_ketgan_sana = date.today()
        super().save(*args, **kwargs)

    @property
    def toliq_ism(self):
        return f"{self.familiya} {self.ism}".strip()

    @property
    def bosh_harflar(self):
        return f"{self.familiya[:1]}{self.ism[:1]}".upper()

    @property
    def saytga_kiradi(self):
        return self.foydalanuvchi is not None and self.foydalanuvchi.saytga_kira_oladi

    @property
    def qoldiq(self):
        """Musbat = xodimga to'lanishi kerak, manfiy = ortiqcha avans berilgan."""
        from .services import xodim_qoldigi
        return xodim_qoldigi(self)


class XodimTranzaksiyaQuerySet(models.QuerySet):
    def tolovlar(self):
        return self.filter(tur__in=[XodimTranzaksiya.Tur.AVANS, XodimTranzaksiya.Tur.OYLIK])


class XodimTranzaksiya(models.Model):
    """Xodimning oylik hisobi va to'lovlari (avans hisob tizimi)."""

    class Tur(models.TextChoices):
        HISOB = "hisob", "Hisoblangan oylik"
        AVANS = "avans", "Avans berildi"
        OYLIK = "oylik", "Oylik berildi"
        BONUS = "bonus", "Bonus / ustama"
        JARIMA = "jarima", "Ushlab qolindi"

    # +1 xodim foydasiga (qarzimiz ortadi), -1 to'lab berdik / ushlab qoldik
    ISHORA = {
        Tur.HISOB: +1,
        Tur.BONUS: +1,
        Tur.AVANS: -1,
        Tur.OYLIK: -1,
        Tur.JARIMA: -1,
    }

    xodim = models.ForeignKey(Xodim, verbose_name="Xodim", on_delete=models.CASCADE,
                              related_name="tranzaksiyalar")
    tur = models.CharField("Turi", max_length=20, choices=Tur.choices)
    summa = models.DecimalField("Summa (so'm)", max_digits=12, decimal_places=2,
                                validators=[MinValueValidator(0)])
    sana = models.DateField("Sana", default=date.today)

    usul = models.CharField("To'lov usuli", max_length=10, choices=Usul.choices, blank=True)
    karta_raqami = models.CharField("Karta raqami", max_length=30, blank=True)

    davr = models.DateField("Hisob davri (oy boshi)", null=True, blank=True)
    kunlar = models.PositiveSmallIntegerField("Hisoblangan kunlar", null=True, blank=True)

    izoh = models.CharField("Izoh", max_length=255, blank=True)
    yaratgan = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Kiritdi",
                                 on_delete=models.SET_NULL, null=True, blank=True)
    yaratilgan = models.DateTimeField(auto_now_add=True)

    objects = XodimTranzaksiyaQuerySet.as_manager()

    class Meta:
        verbose_name = "Xodim tranzaksiyasi"
        verbose_name_plural = "Xodim tranzaksiyalari"
        ordering = ["-sana", "-id"]
        indexes = [models.Index(fields=["tur", "sana"])]
        constraints = [
            models.UniqueConstraint(
                fields=["xodim", "davr"],
                condition=models.Q(tur="hisob"),
                name="xodimga_bir_oyga_bitta_hisob",
            )
        ]

    def __str__(self):
        return f"{self.xodim} - {self.get_tur_display()} - {self.summa}"

    @property
    def ishorali_summa(self):
        return self.summa * self.ISHORA.get(self.tur, 0)

    @property
    def chiqim_mi(self):
        """Kassadan haqiqiy pul chiqqanmi."""
        return self.tur in (self.Tur.AVANS, self.Tur.OYLIK)
