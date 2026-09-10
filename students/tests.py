"""O'qituvchi faqat o'z guruhlarini ko'rishi testlari."""
import re
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Foydalanuvchi
from payments.models import Tranzaksiya, Usul
from staff.models import Xodim

from .models import Guruh, Oquvchi


def oquvchi_yarat(guruh, ism="Ali", familiya="Valiyev"):
    return Oquvchi.objects.create(
        ism=ism, familiya=familiya, telefon="+998901234567",
        guruh=guruh, boshlangan_sana=date(2026, 9, 1),
    )


class OqituvchiKorinishiTest(TestCase):
    """O'qituvchiga faqat o'ziga biriktirilgan guruh o'quvchilari ko'rinadi."""

    def setUp(self):
        self.admin = Foydalanuvchi.objects.create_user(
            username="admin1", password="parol12345", rol=Foydalanuvchi.Rol.ADMIN)

        self.hisob = Foydalanuvchi.objects.create_user(
            username="olim", password="parol12345", rol=Foydalanuvchi.Rol.OQITUVCHI,
            first_name="Olim", last_name="Karimov")
        self.xodim = Xodim.objects.create(ism="Olim", familiya="Karimov",
                                          oylik_maosh=Decimal(0),
                                          foydalanuvchi=self.hisob)

        self.mening = Guruh.objects.create(nomi="11-sinf", oylik_toluv=Decimal(600000),
                                           oqituvchi=self.hisob)
        self.begona = Guruh.objects.create(nomi="9-sinf", oylik_toluv=Decimal(500000))

        self.mening_oquvchim = oquvchi_yarat(self.mening, "Zilola", "Valiyeva")
        self.begona_oquvchi = oquvchi_yarat(self.begona, "Jasur", "Rahmonov")

        self.client.login(username="olim", password="parol12345")

    def test_royxatda_faqat_oz_oquvchilari(self):
        javob = self.client.get(reverse("students:oquvchilar"))
        self.assertContains(javob, "Valiyeva Zilola")
        self.assertNotContains(javob, "Rahmonov Jasur")

    def test_begona_oquvchini_ocha_olmaydi(self):
        javob = self.client.get(
            reverse("students:oquvchi", args=[self.begona_oquvchi.pk]))
        self.assertEqual(javob.status_code, 404)

    def test_oz_oquvchisini_ochadi(self):
        javob = self.client.get(
            reverse("students:oquvchi", args=[self.mening_oquvchim.pk]))
        self.assertEqual(javob.status_code, 200)

    def test_faqat_oz_guruhini_koradi(self):
        javob = self.client.get(reverse("students:guruhlar"))
        self.assertContains(javob, "11-sinf")
        self.assertNotContains(javob, "9-sinf")

    def test_yangi_oquvchi_formasida_faqat_oz_guruhi(self):
        javob = self.client.get(reverse("students:oquvchi_yangi"))
        self.assertEqual(javob.status_code, 200)
        html = javob.content.decode()
        self.assertIn("11-sinf", html)
        self.assertNotIn("9-sinf", html)

    def test_oz_guruhiga_oquvchi_qoshadi(self):
        javob = self.client.post(reverse("students:oquvchi_yangi"), {
            "ism": "Sardor", "familiya": "Aliyev", "telefon": "+998900001122",
            "ota_telefon": "", "ona_telefon": "", "guruh": str(self.mening.pk),
            "oylik_toluv": "", "boshlangan_sana": "2026-09-01", "izoh": "",
        })
        self.assertEqual(javob.status_code, 302)
        yangi = Oquvchi.objects.get(familiya="Aliyev")
        self.assertEqual(yangi.guruh, self.mening)

    def test_begona_guruhga_oquvchi_qosha_olmaydi(self):
        self.client.post(reverse("students:oquvchi_yangi"), {
            "ism": "Sardor", "familiya": "Begonaev", "telefon": "+998900001122",
            "ota_telefon": "", "ona_telefon": "", "guruh": str(self.begona.pk),
            "oylik_toluv": "", "boshlangan_sana": "2026-09-01", "izoh": "",
        })
        self.assertFalse(Oquvchi.objects.filter(familiya="Begonaev").exists())

    def test_oz_oquvchisiga_tolov_qabul_qiladi(self):
        javob = self.client.post(
            reverse("payments:tez_tolov", args=[self.mening_oquvchim.pk]),
            {"usul": Usul.NAQD, "summa": "100 000"})
        self.assertEqual(javob.status_code, 302)
        self.assertTrue(Tranzaksiya.objects.filter(
            oquvchi=self.mening_oquvchim, tur=Tranzaksiya.Tur.TOLOV).exists())

    def test_begona_oquvchiga_tolov_qila_olmaydi(self):
        javob = self.client.post(
            reverse("payments:tez_tolov", args=[self.begona_oquvchi.pk]),
            {"usul": Usul.NAQD, "summa": "100 000"})
        self.assertEqual(javob.status_code, 404)

    def test_tolovlar_royxatida_faqat_ozinikilar(self):
        Tranzaksiya.objects.create(oquvchi=self.begona_oquvchi,
                                   tur=Tranzaksiya.Tur.TOLOV,
                                   summa=Decimal(50000), sana=date(2026, 9, 5),
                                   usul=Usul.NAQD)
        javob = self.client.get(reverse("payments:tolovlar"))
        self.assertNotContains(javob, "Rahmonov Jasur")

    def test_admin_bolimlariga_kira_olmaydi(self):
        for manzil in (reverse("dashboard:moliya"),
                       reverse("students:guruh_yangi"),
                       reverse("staff:xodimlar"),
                       reverse("staff:xodim", args=[self.xodim.pk]),
                       reverse("staff:tolovlar"),
                       reverse("staff:tez_oylik_oyna", args=[self.xodim.pk]),
                       reverse("staff:xodim_yangi")):
            with self.subTest(manzil=manzil):
                self.assertEqual(self.client.get(manzil).status_code, 302)

    def test_bosh_sahifada_oz_guruhlari(self):
        javob = self.client.get(reverse("dashboard:bosh"))
        self.assertEqual(javob.status_code, 200)
        self.assertContains(javob, "Guruhlarim")
        self.assertContains(javob, "11-sinf")
        self.assertNotContains(javob, "9-sinf")

    def test_menyuda_admin_bolimlari_yoq(self):
        html = self.client.get(reverse("dashboard:bosh")).content.decode()
        self.assertIn("Mening o'quvchilarim", html)
        for bolim in ("Oylik va avans", "Moliya (statistika)"):
            self.assertNotIn(bolim, html)


class AdminKorinishiTest(TestCase):
    """Admin hamma guruh va o'quvchini ko'radi, guruhga o'qituvchi biriktiradi."""

    def setUp(self):
        self.admin = Foydalanuvchi.objects.create_user(
            username="admin1", password="parol12345", rol=Foydalanuvchi.Rol.ADMIN)
        self.oqituvchi_hisob = Foydalanuvchi.objects.create_user(
            username="olim", password="parol12345",
            rol=Foydalanuvchi.Rol.OQITUVCHI, first_name="Olim", last_name="Karimov")
        self.xodim = Xodim.objects.create(ism="Olim", familiya="Karimov",
                                          oylik_maosh=Decimal(0),
                                          foydalanuvchi=self.oqituvchi_hisob)
        self.client.login(username="admin1", password="parol12345")

    def test_guruh_yaratib_oqituvchi_biriktiradi(self):
        javob = self.client.post(reverse("students:guruh_yangi"), {
            "nomi": "11-sinf", "oqituvchi": str(self.oqituvchi_hisob.pk),
            "oylik_toluv": "600 000", "faol": "on",
        })
        self.assertEqual(javob.status_code, 302)
        guruh = Guruh.objects.get(nomi="11-sinf")
        self.assertEqual(guruh.oqituvchi, self.oqituvchi_hisob)

    def test_admin_hamma_oquvchini_koradi(self):
        g1 = Guruh.objects.create(nomi="A", oylik_toluv=Decimal(1),
                                  oqituvchi=self.oqituvchi_hisob)
        g2 = Guruh.objects.create(nomi="B", oylik_toluv=Decimal(1))
        oquvchi_yarat(g1, "Zilola", "Valiyeva")
        oquvchi_yarat(g2, "Jasur", "Rahmonov")
        javob = self.client.get(reverse("students:oquvchilar"))
        self.assertContains(javob, "Valiyeva Zilola")
        self.assertContains(javob, "Rahmonov Jasur")


class GuruhOqituvchisiTest(TestCase):
    """O'qituvchi tanlanmasa, guruhni yaratgan admin qayd etiladi."""

    def setUp(self):
        self.admin = Foydalanuvchi.objects.create_user(
            username="admin1", password="parol12345", rol=Foydalanuvchi.Rol.ADMIN,
            first_name="Odil", last_name="Kenjayev")
        self.client.login(username="admin1", password="parol12345")

    def test_oqituvchi_tanlanmasa_admin_qayd_etiladi(self):
        javob = self.client.post(reverse("students:guruh_yangi"), {
            "nomi": "1-guruh", "oqituvchi": "", "oylik_toluv": "600 000", "faol": "on",
        })
        self.assertEqual(javob.status_code, 302)
        guruh = Guruh.objects.get(nomi="1-guruh")
        self.assertEqual(guruh.oqituvchi, self.admin)
        self.assertEqual(guruh.oqituvchi.toliq_ism, "Kenjayev Odil")

    def royxat(self):
        """Formadagi o'qituvchi ro'yxati (<select> ichi)."""
        html = self.client.get(reverse("students:guruh_yangi")).content.decode()
        return re.search(r'<select name="oqituvchi".*?</select>', html, re.S).group(0)

    def test_royxatda_ozi_takrorlanmaydi(self):
        royxat = self.royxat()
        self.assertIn("zim o&#x27;qituvchiman", royxat)
        self.assertNotIn("Kenjayev Odil", royxat)

    def test_boshqa_oqituvchi_royxatda_turadi(self):
        Foydalanuvchi.objects.create_user(
            username="olim", password="parol12345",
            rol=Foydalanuvchi.Rol.OQITUVCHI, first_name="Olim", last_name="Karimov")
        self.assertIn("Karimov Olim", self.royxat())

    def test_admin_oz_guruhini_koradi(self):
        self.client.post(reverse("students:guruh_yangi"), {
            "nomi": "1-guruh", "oqituvchi": "", "oylik_toluv": "600 000", "faol": "on"})
        javob = self.client.get(reverse("students:guruhlar"))
        self.assertContains(javob, "Kenjayev Odil")


class GuruhOynasiTest(TestCase):
    """Guruh ustiga bosilganda undagi o'quvchilar chiqadi."""

    def setUp(self):
        self.admin = Foydalanuvchi.objects.create_user(
            username="admin1", password="parol12345", rol=Foydalanuvchi.Rol.ADMIN)
        self.guruh = Guruh.objects.create(nomi="11-sinf", oylik_toluv=Decimal(600000),
                                          oqituvchi=self.admin)
        self.boshqa = Guruh.objects.create(nomi="9-sinf", oylik_toluv=Decimal(500000),
                                           oqituvchi=self.admin)
        oquvchi_yarat(self.guruh, "Zilola", "Valiyeva")
        oquvchi_yarat(self.boshqa, "Jasur", "Rahmonov")
        self.client.login(username="admin1", password="parol12345")

    def test_oynada_faqat_shu_guruh_oquvchilari(self):
        javob = self.client.get(reverse("students:guruh_oyna", args=[self.guruh.pk]))
        self.assertEqual(javob.status_code, 200)
        self.assertContains(javob, "Valiyeva Zilola")
        self.assertNotContains(javob, "Rahmonov Jasur")

    def test_guruhlar_royxatida_oyna_havolasi_bor(self):
        html = self.client.get(reverse("students:guruhlar")).content.decode()
        self.assertIn("data-oyna=", html)

    def test_oqituvchi_begona_guruh_oynasini_ocha_olmaydi(self):
        hisob = Foydalanuvchi.objects.create_user(
            username="olim", password="parol12345", rol=Foydalanuvchi.Rol.OQITUVCHI)
        self.client.login(username="olim", password="parol12345")
        javob = self.client.get(reverse("students:guruh_oyna", args=[self.guruh.pk]))
        self.assertEqual(javob.status_code, 404)
