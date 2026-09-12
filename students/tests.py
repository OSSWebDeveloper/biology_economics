"""O'qituvchi faqat o'z guruhlarini ko'rishi testlari."""
import re
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Foydalanuvchi
from payments.models import Tranzaksiya, Usul
from staff.models import Xodim

from .models import Arxiv, Guruh, Oquvchi


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


class GuruhniOchirishTest(TestCase):
    """Guruhni tahrirlash sahifasidan o'chirish mumkin."""

    def setUp(self):
        self.admin = Foydalanuvchi.objects.create_user(
            username="admin1", password="parol12345", rol=Foydalanuvchi.Rol.ADMIN)
        self.guruh = Guruh.objects.create(nomi="11-sinf", oylik_toluv=Decimal(600000),
                                          oqituvchi=self.admin)
        self.oquvchi = oquvchi_yarat(self.guruh, "Zilola", "Valiyeva")
        self.client.login(username="admin1", password="parol12345")

    def test_tahrir_sahifasida_ochirish_tugmasi_bor(self):
        html = self.client.get(
            reverse("students:guruh_tahrir", args=[self.guruh.pk])).content.decode()
        self.assertIn(reverse("students:guruh_ochirish", args=[self.guruh.pk]), html)

    def test_yangi_guruh_sahifasida_ochirish_tugmasi_yoq(self):
        html = self.client.get(reverse("students:guruh_yangi")).content.decode()
        self.assertNotIn("Guruhni o'chirish", html)

    def test_ochirilsa_oquvchi_guruhsiz_qoladi(self):
        self.client.post(reverse("students:guruh_ochirish", args=[self.guruh.pk]))
        self.assertFalse(Guruh.objects.filter(pk=self.guruh.pk).exists())
        self.oquvchi.refresh_from_db()
        self.assertIsNone(self.oquvchi.guruh)

    def test_oqituvchi_guruhni_ochira_olmaydi(self):
        Foydalanuvchi.objects.create_user(
            username="olim", password="parol12345", rol=Foydalanuvchi.Rol.OQITUVCHI)
        self.client.login(username="olim", password="parol12345")
        self.client.post(reverse("students:guruh_ochirish", args=[self.guruh.pk]))
        self.assertTrue(Guruh.objects.filter(pk=self.guruh.pk).exists())


class QarzdorlarBolimiTest(TestCase):
    """Ro'yxatdagi "Qarzdorlar" bo'limi."""

    def setUp(self):
        Foydalanuvchi.objects.create_user(
            username="admin1", password="parol12345", rol=Foydalanuvchi.Rol.ADMIN)
        self.guruh = Guruh.objects.create(nomi="11-sinf", oylik_toluv=Decimal(600000))
        self.qarzdor = oquvchi_yarat(self.guruh, "Jasur", "Rahmonov")
        self.tolagan = oquvchi_yarat(self.guruh, "Zilola", "Valiyeva")
        Tranzaksiya.objects.create(
            oquvchi=self.qarzdor, tur=Tranzaksiya.Tur.HISOB, summa=Decimal(600000),
            sana=date(2026, 9, 1), davr=date(2026, 9, 1))
        Tranzaksiya.objects.create(
            oquvchi=self.tolagan, tur=Tranzaksiya.Tur.TOLOV, summa=Decimal(600000),
            sana=date(2026, 9, 5), usul=Usul.NAQD)
        self.client.login(username="admin1", password="parol12345")

    def manzil(self, **parametrlar):
        qoshimcha = "".join(f"&{k}={v}" for k, v in parametrlar.items())
        return reverse("students:oquvchilar") + "?royxat=qarzdor" + qoshimcha

    def test_faqat_qarzdorlar_korinadi(self):
        javob = self.client.get(self.manzil())
        self.assertEqual(javob.status_code, 200)
        self.assertContains(javob, "Rahmonov Jasur")
        self.assertNotContains(javob, "Valiyeva Zilola")

    def test_jami_qarz_hisoblanadi(self):
        javob = self.client.get(self.manzil())
        self.assertContains(javob, "Jami qarz")
        self.assertEqual(javob.context["jamlar"]["qarz_summa"], Decimal(600000))
        self.assertEqual(javob.context["jamlar"]["qarzdor"], 1)

    def test_oddiy_royxatda_bolim_yorligi_bor(self):
        html = self.client.get(reverse("students:oquvchilar")).content.decode()
        self.assertIn("?royxat=qarzdor", html)

    def test_chiqarilgan_qarzdor_faqat_qamrov_bilan_korinadi(self):
        self.qarzdor.faol = False
        self.qarzdor.chiqarilgan_sana = date(2026, 9, 10)
        self.qarzdor.save()
        self.assertNotContains(self.client.get(self.manzil()), "Rahmonov Jasur")
        self.assertContains(
            self.client.get(self.manzil(qamrov="hammasi")), "Rahmonov Jasur")

    def test_hali_tolamaganlar_belgilanadi(self):
        self.assertContains(self.client.get(self.manzil()), "hali to'lamagan")


class ArxivlashTest(TestCase):
    """Arxivlash oynachasi va "Arxiv" bo'limi."""

    def setUp(self):
        Foydalanuvchi.objects.create_user(
            username="admin1", password="parol12345", rol=Foydalanuvchi.Rol.ADMIN)
        self.guruh = Guruh.objects.create(nomi="11-sinf", oylik_toluv=Decimal(600000))
        self.oquvchi = oquvchi_yarat(self.guruh, "Jasur", "Rahmonov")
        self.client.login(username="admin1", password="parol12345")

    def arxivla(self, **maydonlar):
        return self.client.post(
            reverse("students:oquvchi_arxivlash", args=[self.oquvchi.pk]), maydonlar)

    def test_oynacha_ochiladi(self):
        javob = self.client.get(
            reverse("students:oquvchi_arxiv_oyna", args=[self.oquvchi.pk]))
        self.assertEqual(javob.status_code, 200)
        for nomi in ("qishga kirdi", "Sertifikat oldi", "Guruhdan chetlatildi"):
            self.assertContains(javob, nomi)

    def test_oqishga_kirdi_ballari_saqlanadi(self):
        self.arxivla(sabab="oqish", biologiya_bali="78.5", jami_ball="164.3")
        yozuv = Arxiv.objects.get(oquvchi=self.oquvchi)
        self.assertEqual(yozuv.sabab, Arxiv.Sabab.OQISHGA_KIRDI)
        self.assertEqual(yozuv.biologiya_bali, Decimal("78.5"))
        self.assertEqual(yozuv.jami_ball, Decimal("164.3"))
        self.assertEqual(yozuv.guruh_nomi, "11-sinf")
        self.assertEqual(yozuv.guruh, self.guruh)

    def test_arxivlangan_guruhdan_chiqariladi(self):
        self.arxivla(sabab="chetlatildi")
        self.oquvchi.refresh_from_db()
        self.assertIsNone(self.oquvchi.guruh)
        self.assertFalse(self.oquvchi.faol)
        # Guruh olib tashlansa ham oylik narx yo'qolmaydi
        self.assertEqual(self.oquvchi.oylik_toluv, Decimal(600000))
        self.assertEqual(self.guruh.faol_oquvchilar_soni, 0)

    def test_sertifikatsiz_saqlanmaydi(self):
        self.arxivla(sabab="sertifikat", sertifikat="")
        self.assertFalse(Arxiv.objects.exists())

    def test_sertifikat_saqlanadi(self):
        self.arxivla(sabab="sertifikat", sertifikat="A-2026/114")
        yozuv = Arxiv.objects.get(oquvchi=self.oquvchi)
        self.assertEqual(yozuv.sertifikat, "A-2026/114")
        self.assertIsNone(yozuv.biologiya_bali)

    def test_haydalganda_qoshimcha_maydonlar_tozalanadi(self):
        self.arxivla(sabab="chetlatildi", biologiya_bali="90", sertifikat="bor edi")
        yozuv = Arxiv.objects.get(oquvchi=self.oquvchi)
        self.assertEqual(yozuv.sertifikat, "")
        self.assertIsNone(yozuv.biologiya_bali)
        self.assertIsNone(yozuv.jami_ball)

    def test_ballsiz_oqishga_kirdi_saqlanmaydi(self):
        self.arxivla(sabab="oqish", biologiya_bali="", jami_ball="")
        self.assertFalse(Arxiv.objects.exists())

    def test_arxivlangan_royxatda_korinmaydi(self):
        self.arxivla(sabab="chetlatildi")
        self.client.get(reverse("students:oquvchilar"))  # xabarni iste'mol qiladi
        for manzil in ("", "?royxat=chiqarilgan", "?royxat=hammasi",
                       "?royxat=qarzdor&qamrov=hammasi"):
            with self.subTest(manzil=manzil):
                javob = self.client.get(reverse("students:oquvchilar") + manzil)
                self.assertNotContains(javob, "Rahmonov Jasur")
                self.assertNotIn(self.oquvchi, list(javob.context["sahifa"]))

    def test_arxiv_bolimida_korinadi(self):
        self.arxivla(sabab="oqish", biologiya_bali="78.5", jami_ball="164.3")
        javob = self.client.get(reverse("students:arxiv"))
        self.assertContains(javob, "Rahmonov Jasur")
        self.assertContains(javob, "11-sinf")

    def test_yorliqlar_ajratadi(self):
        self.arxivla(sabab="chetlatildi")
        manzil = reverse("students:arxiv")
        self.assertContains(self.client.get(manzil + "?bolim=chetlatildi"), "Rahmonov Jasur")
        self.assertNotContains(self.client.get(manzil + "?bolim=oqish"), "Rahmonov Jasur")

    def test_ikki_marta_arxivlanmaydi(self):
        self.arxivla(sabab="chetlatildi")
        self.arxivla(sabab="oqish", biologiya_bali="80", jami_ball="170")
        self.assertEqual(Arxiv.objects.count(), 1)
        self.assertEqual(Arxiv.objects.get().sabab, Arxiv.Sabab.CHETLATILDI)

    def test_oqituvchi_oz_arxivini_koradi(self):
        oqituvchi = Foydalanuvchi.objects.create_user(
            username="olim", password="parol12345", rol=Foydalanuvchi.Rol.OQITUVCHI)
        self.guruh.oqituvchi = oqituvchi
        self.guruh.save()
        self.arxivla(sabab="chetlatildi")

        self.client.login(username="olim", password="parol12345")
        self.assertContains(self.client.get(reverse("students:arxiv")), "Rahmonov Jasur")
        # Guruhi bo'shatilgan bo'lsa ham kartochkasi ochiladi
        javob = self.client.get(reverse("students:oquvchi", args=[self.oquvchi.pk]))
        self.assertEqual(javob.status_code, 200)

    def test_arxivdan_chiqariladi(self):
        self.arxivla(sabab="chetlatildi")
        yozuv = Arxiv.objects.get()
        self.client.get(reverse("students:oquvchilar"))  # xabarni iste'mol qiladi
        self.client.post(reverse("students:arxivdan_chiqarish", args=[yozuv.pk]))
        self.assertFalse(Arxiv.objects.exists())
        javob = self.client.get(reverse("students:oquvchilar") + "?royxat=chiqarilgan")
        self.assertContains(javob, "Rahmonov Jasur")


class GuruhKochirishTest(TestCase):
    """O'quvchini bir guruhdan boshqasiga o'tkazish."""

    def setUp(self):
        Foydalanuvchi.objects.create_user(
            username="admin1", password="parol12345", rol=Foydalanuvchi.Rol.ADMIN)
        self.eski = Guruh.objects.create(nomi="9-sinf", oylik_toluv=Decimal(500000))
        self.yangi = Guruh.objects.create(nomi="11-sinf", oylik_toluv=Decimal(700000))
        self.oquvchi = oquvchi_yarat(self.eski, "Jasur", "Rahmonov")
        Tranzaksiya.objects.create(
            oquvchi=self.oquvchi, tur=Tranzaksiya.Tur.TOLOV, summa=Decimal(300000),
            sana=date(2026, 9, 5), usul=Usul.NAQD)
        self.client.login(username="admin1", password="parol12345")

    def kochir(self, **maydonlar):
        return self.client.post(
            reverse("students:oquvchi_guruh_kochirish", args=[self.oquvchi.pk]),
            maydonlar)

    def test_oynacha_ochiladi(self):
        javob = self.client.get(
            reverse("students:oquvchi_guruh_oyna", args=[self.oquvchi.pk]))
        self.assertEqual(javob.status_code, 200)
        # Yangi guruh narxi bilan ko'rinadi, hozirgi guruh ro'yxatda yo'q
        self.assertContains(javob, "11-sinf - 700 000")
        self.assertNotContains(javob, "9-sinf - 500 000")

    def test_yangi_guruh_narxi_qollanadi(self):
        self.kochir(guruh=str(self.yangi.pk), narx="yangi")
        self.oquvchi.refresh_from_db()
        self.assertEqual(self.oquvchi.guruh, self.yangi)
        self.assertIsNone(self.oquvchi.oylik_toluv)
        self.assertEqual(self.oquvchi.amaldagi_oylik, Decimal(700000))

    def test_eski_narx_saqlanadi(self):
        self.kochir(guruh=str(self.yangi.pk), narx="eski")
        self.oquvchi.refresh_from_db()
        self.assertEqual(self.oquvchi.guruh, self.yangi)
        self.assertEqual(self.oquvchi.amaldagi_oylik, Decimal(500000))

    def test_tolovlar_tarixi_saqlanadi(self):
        self.kochir(guruh=str(self.yangi.pk), narx="yangi")
        self.assertEqual(self.oquvchi.tranzaksiyalar.count(), 1)
        self.assertEqual(self.oquvchi.balans, Decimal(300000))

    def test_guruhsiz_yuborilsa_ozgarmaydi(self):
        self.kochir(guruh="", narx="yangi")
        self.oquvchi.refresh_from_db()
        self.assertEqual(self.oquvchi.guruh, self.eski)

    def test_oqituvchi_begona_guruhga_kochira_olmaydi(self):
        oqituvchi = Foydalanuvchi.objects.create_user(
            username="olim", password="parol12345", rol=Foydalanuvchi.Rol.OQITUVCHI)
        self.eski.oqituvchi = oqituvchi
        self.eski.save()
        self.client.login(username="olim", password="parol12345")
        self.kochir(guruh=str(self.yangi.pk), narx="yangi")
        self.oquvchi.refresh_from_db()
        self.assertEqual(self.oquvchi.guruh, self.eski)

    def test_kartochkada_tugma_bor(self):
        javob = self.client.get(reverse("students:oquvchi", args=[self.oquvchi.pk]))
        self.assertContains(javob, "Guruhni o'zgartirish")
        self.assertContains(
            javob, reverse("students:oquvchi_guruh_oyna", args=[self.oquvchi.pk]))
