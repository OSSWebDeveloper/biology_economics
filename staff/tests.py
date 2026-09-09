"""Xodimlar oyligi va avans hisobining testlari."""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from payments.models import Usul

from .models import Xodim, XodimTranzaksiya
from .services import (
    joriy_oy_avansi,
    maosh_summasi,
    maoshlarni_yangila,
    qoldiq_holati,
    xodim_qoldigi,
)

SENTABR = date(2025, 9, 1)


def xodim_yarat(ishga_kirgan=SENTABR, maosh=3000000, **qoshimcha):
    return Xodim.objects.create(
        ism="Olim", familiya="Karimov", lavozim="o'qituvchi",
        oylik_maosh=Decimal(maosh), ishga_kirgan_sana=ishga_kirgan, **qoshimcha,
    )


class MaoshHisobiTest(TestCase):
    def test_toliq_oy_uchun_toliq_maosh(self):
        xodim = xodim_yarat()
        summa, kunlar = maosh_summasi(xodim, SENTABR)
        self.assertEqual(summa, Decimal(3000000))
        self.assertEqual(kunlar, 30)

    def test_oy_ortasida_ishga_kirgan_kunlab_oladi(self):
        xodim = xodim_yarat(ishga_kirgan=date(2025, 9, 21))
        summa, kunlar = maosh_summasi(xodim, SENTABR)
        self.assertEqual(kunlar, 10)
        self.assertEqual(summa, Decimal(1000000))   # 100 000 * 10

    def test_maosh_takrorlanmaydi(self):
        xodim_yarat()
        maoshlarni_yangila(sanagacha=date(2025, 10, 15))
        birinchi = XodimTranzaksiya.objects.count()
        maoshlarni_yangila(sanagacha=date(2025, 10, 15))
        self.assertEqual(XodimTranzaksiya.objects.count(), birinchi)
        self.assertEqual(birinchi, 2)   # sentabr va oktabr


class AvansTest(TestCase):
    def setUp(self):
        self.xodim = xodim_yarat()
        maoshlarni_yangila(sanagacha=date(2025, 9, 20))

    def test_hisoblangan_maosh_qarz_sifatida_turadi(self):
        qoldiq = xodim_qoldigi(self.xodim)
        self.assertEqual(qoldiq, Decimal(3000000))
        self.assertEqual(qoldiq_holati(qoldiq)["kod"], "qarzimiz")

    def test_avans_qoldiqni_kamaytiradi(self):
        XodimTranzaksiya.objects.create(
            xodim=self.xodim, tur=XodimTranzaksiya.Tur.AVANS,
            summa=Decimal(1000000), sana=date(2025, 9, 15), usul=Usul.NAQD,
        )
        self.assertEqual(xodim_qoldigi(self.xodim), Decimal(2000000))
        self.assertEqual(joriy_oy_avansi(self.xodim, SENTABR), Decimal(1000000))

    def test_avans_va_oylik_birga_hisobni_yopadi(self):
        XodimTranzaksiya.objects.create(
            xodim=self.xodim, tur=XodimTranzaksiya.Tur.AVANS,
            summa=Decimal(1000000), sana=date(2025, 9, 15), usul=Usul.NAQD,
        )
        XodimTranzaksiya.objects.create(
            xodim=self.xodim, tur=XodimTranzaksiya.Tur.OYLIK,
            summa=Decimal(2000000), sana=date(2025, 10, 1), usul=Usul.PLASTIK,
            karta_raqami="8600111122223333",
        )
        qoldiq = xodim_qoldigi(self.xodim)
        self.assertEqual(qoldiq, Decimal(0))
        self.assertEqual(qoldiq_holati(qoldiq)["kod"], "toza")

    def test_ortiqcha_avans_manfiy_qoldiq_beradi(self):
        XodimTranzaksiya.objects.create(
            xodim=self.xodim, tur=XodimTranzaksiya.Tur.AVANS,
            summa=Decimal(3500000), sana=date(2025, 9, 15), usul=Usul.NAQD,
        )
        qoldiq = xodim_qoldigi(self.xodim)
        self.assertEqual(qoldiq, Decimal(-500000))
        self.assertEqual(qoldiq_holati(qoldiq)["kod"], "ortiqcha")

    def test_ushlab_qolish_qoldiqni_kamaytiradi(self):
        XodimTranzaksiya.objects.create(
            xodim=self.xodim, tur=XodimTranzaksiya.Tur.JARIMA,
            summa=Decimal(200000), sana=date(2025, 9, 25),
        )
        self.assertEqual(xodim_qoldigi(self.xodim), Decimal(2800000))
