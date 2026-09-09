"""Sahifalar ochilishini va kirish huquqlarini tekshiruvchi testlar."""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Foydalanuvchi
from payments.models import Karta, Tranzaksiya, Usul
from staff.models import Xodim
from students.models import Guruh, Oquvchi


class KirishTest(TestCase):
    def setUp(self):
        self.admin = Foydalanuvchi.objects.create_user(
            username="sayt_admin", password="parol12345",
            rol=Foydalanuvchi.Rol.ADMIN, first_name="Sayt", last_name="Admini",
        )
        self.texnik = Foydalanuvchi.objects.create_superuser(
            username="texnik", password="parol12345",
        )
        self.texnik.saytga_kira_oladi = False
        self.texnik.save(update_fields=["saytga_kira_oladi"])

    def test_kirmagan_foydalanuvchi_kirish_sahifasiga_yonaltiriladi(self):
        javob = self.client.get(reverse("dashboard:bosh"))
        self.assertEqual(javob.status_code, 302)
        self.assertIn(reverse("accounts:kirish"), javob["Location"])

    def test_sayt_admini_kira_oladi(self):
        kirdi = self.client.login(username="sayt_admin", password="parol12345")
        self.assertTrue(kirdi)
        self.assertEqual(self.client.get(reverse("dashboard:bosh")).status_code, 200)

    def test_django_admin_superuseri_sayt_paneliga_kira_olmaydi(self):
        """Django admin va sayt paneli hisoblari bir-biridan alohida."""
        javob = self.client.post(reverse("accounts:kirish"), {
            "username": "texnik", "password": "parol12345",
        })
        self.assertEqual(javob.status_code, 200)          # qayta forma ko'rsatiladi
        self.assertFalse(javob.wsgi_request.user.is_authenticated)

    def test_sayt_admini_django_adminga_kira_olmaydi(self):
        self.client.login(username="sayt_admin", password="parol12345")
        javob = self.client.get("/boshqaruv/", follow=True)
        self.assertContains(javob, "id_username")        # admin login formasi


class SahifalarTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Foydalanuvchi.objects.create_user(
            username="admin1", password="parol12345", rol=Foydalanuvchi.Rol.ADMIN,
        )
        cls.operator = Foydalanuvchi.objects.create_user(
            username="operator1", password="parol12345",
            rol=Foydalanuvchi.Rol.OPERATOR,
        )
        cls.guruh = Guruh.objects.create(nomi="11-sinf", oylik_toluv=Decimal(600000))
        cls.karta = Karta.objects.create(nomi="Humo", raqam="8600123412341234")
        cls.oquvchi = Oquvchi.objects.create(
            ism="Ali", familiya="Valiyev", telefon="+998901112233",
            ota_telefon="+998901112234", guruh=cls.guruh,
            oylik_toluv=Decimal(600000), boshlangan_sana=date(2025, 9, 15),
        )
        cls.xodim = Xodim.objects.create(
            ism="Olim", familiya="Karimov", oylik_maosh=Decimal(3000000),
            ishga_kirgan_sana=date(2025, 9, 1),
        )

    def setUp(self):
        self.client.login(username="admin1", password="parol12345")

    def test_barcha_asosiy_sahifalar_ochiladi(self):
        manzillar = [
            reverse("dashboard:bosh"),
            reverse("dashboard:moliya"),
            reverse("students:oquvchilar"),
            reverse("students:oquvchilar") + "?holat=qarzdor&tartib=balans",
            reverse("students:oquvchi", args=[self.oquvchi.pk]),
            reverse("students:oquvchi_oyna", args=[self.oquvchi.pk]),
            reverse("students:oquvchi_yangi"),
            reverse("students:oquvchi_tahrir", args=[self.oquvchi.pk]),
            reverse("students:guruhlar"),
            reverse("students:guruh_yangi"),
            reverse("payments:tolovlar"),
            reverse("payments:tolovlar") + "?usul=naqd&tur=tolov",
            reverse("payments:kartalar"),
            reverse("staff:xodimlar"),
            reverse("staff:xodim", args=[self.xodim.pk]),
            reverse("staff:xodim_oyna", args=[self.xodim.pk]),
            reverse("staff:tolovlar"),
            reverse("accounts:shaxsiy"),
        ]
        for manzil in manzillar:
            with self.subTest(manzil=manzil):
                self.assertEqual(self.client.get(manzil).status_code, 200)

    def test_operator_admin_bolimlariga_kira_olmaydi(self):
        self.client.login(username="operator1", password="parol12345")
        for manzil in (reverse("payments:kartalar"), reverse("students:guruh_yangi")):
            with self.subTest(manzil=manzil):
                self.assertEqual(self.client.get(manzil).status_code, 302)

    def test_tolov_qoshiladi_va_balans_ozgaradi(self):
        javob = self.client.post(
            reverse("payments:tolov_qoshish", args=[self.oquvchi.pk]),
            {"tur": "tolov", "summa": "320000", "sana": "2025-09-15",
             "usul": Usul.PLASTIK, "karta": self.karta.pk, "karta_raqami": "",
             "izoh": "sentabr uchun"},
        )
        self.assertEqual(javob.status_code, 302)
        tolov = Tranzaksiya.objects.get(oquvchi=self.oquvchi, tur=Tranzaksiya.Tur.TOLOV)
        self.assertEqual(tolov.summa, Decimal(320000))
        self.assertEqual(tolov.karta_raqami, self.karta.raqam)

    def test_plastik_tolov_kartasiz_saqlanmaydi(self):
        self.client.post(
            reverse("payments:tolov_qoshish", args=[self.oquvchi.pk]),
            {"tur": "tolov", "summa": "100000", "sana": "2025-09-15",
             "usul": Usul.PLASTIK},
        )
        self.assertFalse(
            Tranzaksiya.objects.filter(tur=Tranzaksiya.Tur.TOLOV).exists()
        )

    def test_oquvchini_royxatdan_chiqarish(self):
        javob = self.client.post(
            reverse("students:oquvchi_chiqarish", args=[self.oquvchi.pk]),
            {"chiqarilgan_sana": "2025-09-20", "sabab": "ko'chib ketdi",
             "qayta_hisobla": "on"},
        )
        self.assertEqual(javob.status_code, 302)
        self.oquvchi.refresh_from_db()
        self.assertFalse(self.oquvchi.faol)
        self.assertEqual(self.oquvchi.chiqarilgan_sana, date(2025, 9, 20))
        # 15-20 sentabr = 6 kun * 20 000 = 120 000
        hisob = Tranzaksiya.objects.get(oquvchi=self.oquvchi,
                                        tur=Tranzaksiya.Tur.HISOB)
        self.assertEqual(hisob.kunlar, 6)
        self.assertEqual(hisob.summa, Decimal(120000))

    def test_xodimga_avans_beriladi(self):
        javob = self.client.post(
            reverse("staff:tolov_qoshish", args=[self.xodim.pk]),
            {"tur": "avans", "summa": "500000", "sana": "2025-09-15",
             "usul": Usul.NAQD},
        )
        self.assertEqual(javob.status_code, 302)
        self.assertEqual(self.xodim.tranzaksiyalar.filter(tur="avans").count(), 1)

    def test_admin_xodim_oyligini_tayinlaydi(self):
        javob = self.client.post(
            reverse("staff:maosh_tayinlash", args=[self.xodim.pk]),
            {"oylik_maosh": "4000000", "qayta_hisobla": "on"},
        )
        self.assertEqual(javob.status_code, 302)
        self.xodim.refresh_from_db()
        self.assertEqual(self.xodim.oylik_maosh, Decimal(4000000))

    def test_operator_xodim_oyligini_tayinlay_olmaydi(self):
        self.client.login(username="operator1", password="parol12345")
        self.client.post(
            reverse("staff:maosh_tayinlash", args=[self.xodim.pk]),
            {"oylik_maosh": "9000000"},
        )
        self.xodim.refresh_from_db()
        self.assertEqual(self.xodim.oylik_maosh, Decimal(3000000))
