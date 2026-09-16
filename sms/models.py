"""SMS moduli: qurilmalar, ulanish kodlari va xabarlar navbati.

Ish tartibi:
  1. Admin "Xabarnoma" bo'limida 12 xonalik ulanish kodi chiqaradi.
  2. Telefondagi ilova shu kodni yuboradi va o'ziga doimiy kalit oladi
     (`Qurilma.kalit`) - bundan keyin barcha so'rovlar shu kalit bilan.
  3. Har oyning 1-sanasida qarzdorlarga xabarlar navbatga yoziladi
     (holat = "navbatda", hali hech qaysi qurilmaga berilmagan).
  4. Admin "Xabarlar" bo'limida qurilma/SIM larni belgilab "Yuborish" ni
     bosadi - xabarlar tanlangan kanallarga teng bo'linadi (holat = "berildi").
  5. Ilova o'ziga tegishli xabarlarni olib jo'natadi va natijani qaytaradi.
"""
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from students.models import Oquvchi


class Qurilma(models.Model):
    """Saytga ulangan telefon."""

    ONLAYN_DAQIQA = 20   # shuncha vaqt ichida aloqa bo'lgan bo'lsa - onlayn

    qurilma_id = models.CharField(
        "Qurilma belgisi", max_length=64, unique=True,
        help_text="Ilova o'rnatilganda bir marta yaratiladigan barqaror belgi.",
    )
    nomi = models.CharField("Nomi", max_length=100)
    ishlab_chiqaruvchi = models.CharField("Ishlab chiqaruvchi", max_length=60, blank=True)
    model = models.CharField("Modeli", max_length=60, blank=True)
    android = models.CharField("Android", max_length=20, blank=True)
    ilova_versiya = models.CharField("Ilova versiyasi", max_length=20, blank=True)

    kalit = models.CharField("Maxfiy kalit", max_length=64, unique=True, db_index=True)

    faol = models.BooleanField(
        "Faol", default=True,
        help_text="O'chirilsa, qurilma saytga ulana olmaydi va SMS ololmaydi.",
    )
    batareya = models.PositiveSmallIntegerField("Batareya (%)", null=True, blank=True)

    qoshilgan = models.DateTimeField("Ulangan vaqt", auto_now_add=True)
    oxirgi_aloqa = models.DateTimeField("Oxirgi aloqa", null=True, blank=True)

    class Meta:
        verbose_name = "Qurilma"
        verbose_name_plural = "Qurilmalar"
        ordering = ["-oxirgi_aloqa", "nomi"]

    def __str__(self):
        return self.nomi

    @staticmethod
    def kalit_yarat():
        return secrets.token_urlsafe(32)

    @property
    def onlayn(self):
        if not self.oxirgi_aloqa:
            return False
        chegara = timezone.now() - timedelta(minutes=self.ONLAYN_DAQIQA)
        return self.oxirgi_aloqa >= chegara

    @property
    def holat_kodi(self):
        if not self.faol:
            return "ochiq"
        return "onlayn" if self.onlayn else "oflayn"

    @property
    def holat_nomi(self):
        return {"ochiq": "O'chirilgan", "onlayn": "Onlayn", "oflayn": "Oflayn"}[self.holat_kodi]

    @property
    def aloqa_matni(self):
        """Oxirgi aloqa qancha vaqt oldin bo'lganini odamcha yozadi."""
        if not self.oxirgi_aloqa:
            return "hali aloqa bo'lmagan"
        farq = timezone.now() - self.oxirgi_aloqa
        daqiqa = int(farq.total_seconds() // 60)
        if daqiqa < 1:
            return "hozirgina"
        if daqiqa < 60:
            return f"{daqiqa} daqiqa oldin"
        soat = daqiqa // 60
        if soat < 24:
            return f"{soat} soat oldin"
        return f"{soat // 24} kun oldin"

    @property
    def tanlanadigan_simlar(self):
        """SMS yuborish uchun ishlatsa bo'ladigan SIM kartalar."""
        return self.simlar.filter(faol=True)


class SimKarta(models.Model):
    """Qurilmadagi bitta SIM karta."""

    qurilma = models.ForeignKey(Qurilma, verbose_name="Qurilma", on_delete=models.CASCADE,
                                related_name="simlar")
    sim_id = models.IntegerField("SIM belgisi (subscriptionId)")
    nomi = models.CharField("Nomi", max_length=60)
    raqam = models.CharField("Raqami", max_length=30, blank=True)
    slot = models.PositiveSmallIntegerField("Uyasi", default=0)
    faol = models.BooleanField("Ishlatilsin", default=True)

    class Meta:
        verbose_name = "SIM karta"
        verbose_name_plural = "SIM kartalar"
        ordering = ["qurilma", "slot"]
        constraints = [
            models.UniqueConstraint(fields=["qurilma", "sim_id"], name="qurilmada_bitta_sim")
        ]

    def __str__(self):
        return f"{self.qurilma.nomi} - {self.nomi}"

    @property
    def toliq_nomi(self):
        return f"{self.nomi} ({self.raqam})" if self.raqam else self.nomi


class UlanishKodi(models.Model):
    """Telefonni saytga ulash uchun 12 xonalik bir martalik kod."""

    AMAL_DAQIQA = 15

    kod = models.CharField("Kod", max_length=12, unique=True)
    yaratgan = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Yaratdi",
                                 on_delete=models.SET_NULL, null=True, blank=True)
    yaratilgan = models.DateTimeField("Yaratilgan", auto_now_add=True)
    amal_qiladi = models.DateTimeField("Amal qilish muddati")

    qurilma = models.ForeignKey(Qurilma, verbose_name="Ulangan qurilma",
                                on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="kodlar")
    ishlatilgan = models.DateTimeField("Ishlatilgan", null=True, blank=True)

    class Meta:
        verbose_name = "Ulanish kodi"
        verbose_name_plural = "Ulanish kodlari"
        ordering = ["-yaratilgan"]

    def __str__(self):
        return self.korinish

    @classmethod
    def yarat(cls, foydalanuvchi=None):
        """Yangi kod yaratadi. Eski ishlatilmagan kodlar bekor qilinadi."""
        cls.objects.filter(ishlatilgan__isnull=True).delete()
        kod = "".join(secrets.choice("0123456789") for _ in range(12))
        return cls.objects.create(
            kod=kod,
            yaratgan=foydalanuvchi,
            amal_qiladi=timezone.now() + timedelta(minutes=cls.AMAL_DAQIQA),
        )

    @property
    def korinish(self):
        """Ekranda o'qish oson bo'lishi uchun: 1234 5678 9012."""
        return f"{self.kod[:4]} {self.kod[4:8]} {self.kod[8:]}"

    @property
    def yaroqli(self):
        return self.ishlatilgan is None and timezone.now() < self.amal_qiladi

    @property
    def qolgan_soniya(self):
        if not self.yaroqli:
            return 0
        return max(0, int((self.amal_qiladi - timezone.now()).total_seconds()))


class Bildirishnoma(models.Model):
    """Saytda ko'rsatiladigan hodisa: qurilma ulandi, xabar ketmadi va h.k."""

    class Turi(models.TextChoices):
        ULANDI = "ulandi", "Qurilma ulandi"
        UZILDI = "uzildi", "Qurilma uzildi"
        YUBORILDI = "yuborildi", "Xabarlar yuborildi"
        XATO = "xato", "Xatolik"
        MALUMOT = "malumot", "Ma'lumot"

    turi = models.CharField("Turi", max_length=20, choices=Turi.choices,
                            default=Turi.MALUMOT)
    matn = models.CharField("Matn", max_length=255)
    qurilma = models.ForeignKey(Qurilma, verbose_name="Qurilma", on_delete=models.SET_NULL,
                                null=True, blank=True, related_name="bildirishnomalar")
    yaratilgan = models.DateTimeField("Vaqti", auto_now_add=True)
    korildi = models.BooleanField("Ko'rildi", default=False)

    class Meta:
        verbose_name = "Bildirishnoma"
        verbose_name_plural = "Bildirishnomalar"
        ordering = ["-yaratilgan", "-id"]
        indexes = [models.Index(fields=["korildi"])]

    def __str__(self):
        return self.matn

    @classmethod
    def qosh(cls, turi, matn, qurilma=None):
        return cls.objects.create(turi=turi, matn=matn[:255], qurilma=qurilma)


class SmsXabar(models.Model):
    """Bitta qabul qiluvchiga, bitta oy uchun yoziladigan bitta xabar."""

    class Qabul(models.TextChoices):
        OTA = "ota", "Ota"
        ONA = "ona", "Ona"

    class Holat(models.TextChoices):
        NAVBATDA = "navbatda", "Navbatda (yuborilmagan)"
        BERILDI = "berildi", "Qurilmaga berildi"
        OLINDI = "olindi", "Ilova oldi"
        JONATILDI = "jonatildi", "Jo'natildi"
        XATO = "xato", "Xato"
        BEKOR = "bekor", "Bekor qilindi"

    # Ilova olib, javob qaytarmasa shuncha daqiqadan keyin qayta beriladi
    QAYTA_BERISH_DAQIQA = 30

    oquvchi = models.ForeignKey(
        Oquvchi, verbose_name="O'quvchi", on_delete=models.CASCADE,
        related_name="sms_xabarlar",
    )
    qabul_qiluvchi = models.CharField("Kimga", max_length=10, choices=Qabul.choices)
    telefon = models.CharField("Telefon", max_length=30)
    matn = models.TextField("Xabar matni")

    davr = models.DateField("Qaysi oy uchun (oy boshi)")
    summa = models.DecimalField("O'sha paytdagi qarz", max_digits=12, decimal_places=2,
                                default=0)

    holat = models.CharField("Holati", max_length=15, choices=Holat.choices,
                             default=Holat.NAVBATDA)

    qurilma = models.ForeignKey(Qurilma, verbose_name="Qaysi qurilmadan",
                                on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="xabarlar")
    sim = models.ForeignKey(SimKarta, verbose_name="Qaysi SIM dan",
                            on_delete=models.SET_NULL, null=True, blank=True,
                            related_name="xabarlar")
    berilgan = models.DateTimeField("Qurilmaga berilgan vaqt", null=True, blank=True)

    urinishlar = models.PositiveSmallIntegerField("Urinishlar", default=0)
    xato_matni = models.CharField("Xato izohi", max_length=255, blank=True)

    yaratilgan = models.DateTimeField("Navbatga qo'yilgan", auto_now_add=True)
    olingan = models.DateTimeField("Ilova olgan vaqt", null=True, blank=True)
    jonatilgan = models.DateTimeField("Jo'natilgan vaqt", null=True, blank=True)

    class Meta:
        verbose_name = "SMS xabar"
        verbose_name_plural = "SMS xabarlar"
        ordering = ["-davr", "-id"]
        indexes = [
            models.Index(fields=["holat"]),
            models.Index(fields=["davr"]),
            models.Index(fields=["qurilma", "holat"]),
        ]
        constraints = [
            # Bir oyda bitta o'quvchi uchun otaga bitta, onaga bitta xabar.
            models.UniqueConstraint(
                fields=["oquvchi", "davr", "qabul_qiluvchi"],
                name="oyiga_bitta_sms",
            )
        ]

    def __str__(self):
        return f"{self.oquvchi} - {self.get_qabul_qiluvchi_display()} - {self.telefon}"

    @property
    def tugadi(self):
        return self.holat in (self.Holat.JONATILDI, self.Holat.BEKOR)

    @property
    def kutmoqda(self):
        """Hali yuborilmagan - admin qurilma tanlashi kerak."""
        return self.holat == self.Holat.NAVBATDA

    @property
    def holat_rangi(self):
        return {
            self.Holat.NAVBATDA: "kulrang",
            self.Holat.BERILDI: "kok",
            self.Holat.OLINDI: "sariq",
            self.Holat.JONATILDI: "yashil",
            self.Holat.XATO: "qizil",
            self.Holat.BEKOR: "kulrang",
        }.get(self.holat, "kulrang")
