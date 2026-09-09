"""Xodimlar oyligi, avansi va sayt hisobining testlari."""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Foydalanuvchi
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


class XodimHisobiTest(TestCase):
    """Xodimning saytga kirish logini uning kartochkasidan boshqariladi."""

    def setUp(self):
        self.admin = Foydalanuvchi.objects.create_user(
            username="admin1", password="parol12345", rol=Foydalanuvchi.Rol.ADMIN)
        self.xodim = xodim_yarat()
        self.client.login(username="admin1", password="parol12345")

    def _hisob_url(self):
        return reverse("staff:xodim_hisob", args=[self.xodim.pk])

    def test_xodimga_login_yaratiladi(self):
        javob = self.client.post(self._hisob_url(), {
            "login": "olim", "parol": "kurs2026", "rol": Foydalanuvchi.Rol.OPERATOR,
        })
        self.assertEqual(javob.status_code, 302)
        self.xodim.refresh_from_db()
        hisob = self.xodim.foydalanuvchi
        self.assertIsNotNone(hisob)
        self.assertEqual(hisob.username, "olim")
        self.assertTrue(hisob.check_password("kurs2026"))
        self.assertEqual(hisob.toliq_ism, "Karimov Olim")   # ism xodimdan olinadi
        self.assertTrue(self.xodim.saytga_kiradi)

    def test_yaratilgan_login_bilan_saytga_kiriladi(self):
        self.client.post(self._hisob_url(), {
            "login": "olim", "parol": "kurs2026", "rol": Foydalanuvchi.Rol.OPERATOR})
        self.client.logout()
        javob = self.client.post(reverse("accounts:kirish"),
                                 {"username": "olim", "password": "kurs2026"})
        self.assertEqual(javob.status_code, 302)   # muvaffaqiyatli kirish

    def test_parol_va_login_ozgartiriladi(self):
        self.client.post(self._hisob_url(), {
            "login": "olim", "parol": "kurs2026", "rol": Foydalanuvchi.Rol.OPERATOR})
        self.client.post(self._hisob_url(), {
            "login": "olim_yangi", "parol": "boshqa77", "rol": Foydalanuvchi.Rol.ADMIN})
        self.xodim.refresh_from_db()
        hisob = self.xodim.foydalanuvchi
        self.assertEqual(hisob.username, "olim_yangi")
        self.assertTrue(hisob.check_password("boshqa77"))
        self.assertEqual(hisob.rol, Foydalanuvchi.Rol.ADMIN)

    def test_parol_bosh_qoldirilsa_ozgarmaydi(self):
        self.client.post(self._hisob_url(), {
            "login": "olim", "parol": "kurs2026", "rol": Foydalanuvchi.Rol.OPERATOR})
        self.client.post(self._hisob_url(), {
            "login": "olim", "parol": "", "rol": Foydalanuvchi.Rol.OPERATOR})
        self.xodim.refresh_from_db()
        self.assertTrue(self.xodim.foydalanuvchi.check_password("kurs2026"))

    def test_band_login_qabul_qilinmaydi(self):
        self.client.post(self._hisob_url(), {
            "login": "admin1", "parol": "kurs2026", "rol": Foydalanuvchi.Rol.OPERATOR})
        self.xodim.refresh_from_db()
        self.assertIsNone(self.xodim.foydalanuvchi)

    def test_xodim_ismi_ozgarsa_hisob_ismi_ham_ozgaradi(self):
        self.client.post(self._hisob_url(), {
            "login": "olim", "parol": "kurs2026", "rol": Foydalanuvchi.Rol.OPERATOR})
        self.client.post(reverse("staff:xodim_tahrir", args=[self.xodim.pk]), {
            "ism": "Olimjon", "familiya": "Karimov", "lavozim": "o'qituvchi",
            "telefon": "+998 90 000 00 00", "karta_raqami": "",
            "oylik_maosh": "3000000", "ishga_kirgan_sana": "2025-09-01", "izoh": "",
        })
        self.xodim.refresh_from_db()
        self.assertEqual(self.xodim.foydalanuvchi.toliq_ism, "Karimov Olimjon")

    def test_mavjud_hisob_boglanadi(self):
        mavjud = Foydalanuvchi.objects.create_user(
            username="eski", password="parol12345", rol=Foydalanuvchi.Rol.OPERATOR)
        javob = self.client.post(
            reverse("staff:xodim_hisob_boglash", args=[self.xodim.pk]),
            {"hisob": mavjud.pk})
        self.assertEqual(javob.status_code, 302)
        self.xodim.refresh_from_db()
        self.assertEqual(self.xodim.foydalanuvchi, mavjud)

    def test_kirish_huquqi_olib_tashlanadi(self):
        self.client.post(self._hisob_url(), {
            "login": "olim", "parol": "kurs2026", "rol": Foydalanuvchi.Rol.OPERATOR})
        self.client.post(reverse("staff:xodim_hisob_uzish", args=[self.xodim.pk]))
        self.xodim.refresh_from_db()
        self.assertIsNone(self.xodim.foydalanuvchi)
        hisob = Foydalanuvchi.objects.get(username="olim")
        self.assertFalse(hisob.saytga_kira_oladi)
        # kirish sahifasi orqali ham kira olmaydi
        self.client.logout()
        javob = self.client.post(reverse("accounts:kirish"),
                                 {"username": "olim", "password": "kurs2026"})
        self.assertEqual(javob.status_code, 200)   # forma qayta ko'rsatiladi
        self.assertFalse(javob.wsgi_request.user.is_authenticated)

    def test_operator_login_yarata_olmaydi(self):
        operator = Foydalanuvchi.objects.create_user(
            username="oper", password="parol12345", rol=Foydalanuvchi.Rol.OPERATOR)
        self.client.login(username="oper", password="parol12345")
        self.client.post(self._hisob_url(), {
            "login": "olim", "parol": "kurs2026", "rol": Foydalanuvchi.Rol.ADMIN})
        self.xodim.refresh_from_db()
        self.assertIsNone(self.xodim.foydalanuvchi)
