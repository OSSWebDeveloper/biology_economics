"""Shaxsiy sahifa testlari."""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from staff.models import Xodim

from .models import Foydalanuvchi


def foydalanuvchi(login, rol=Foydalanuvchi.Rol.OPERATOR, parol="parol12345", **qo):
    return Foydalanuvchi.objects.create_user(username=login, password=parol, rol=rol, **qo)


class ShaxsiySahifaTest(TestCase):
    def setUp(self):
        self.admin = foydalanuvchi("admin1", Foydalanuvchi.Rol.ADMIN,
                                   first_name="Odil", last_name="Kenjayev")
        self.operator = foydalanuvchi("operator1", first_name="Sanjar",
                                      last_name="Rustamov")
        self.client.login(username="operator1", password="parol12345")

    def test_sahifa_ochiladi(self):
        javob = self.client.get(reverse("accounts:shaxsiy"))
        self.assertEqual(javob.status_code, 200)
        self.assertContains(javob, "Ma'lumotlarim")
        self.assertContains(javob, "Parolni o'zgartirish")

    def test_boshqa_foydalanuvchilar_royxati_yoq(self):
        """Boshqa hisoblar bu sahifada ko'rinmaydi - ular xodim kartochkasida."""
        self.client.login(username="admin1", password="parol12345")
        javob = self.client.get(reverse("accounts:shaxsiy"))
        self.assertNotContains(javob, "Boshqa foydalanuvchilar")
        self.assertNotContains(javob, "operator1")

    def test_oz_ismini_va_loginini_ozgartiradi(self):
        javob = self.client.post(reverse("accounts:shaxsiy"), {
            "amal": "malumot", "last_name": "Rustamova", "first_name": "Sanobar",
            "telefon": "+998 90 111 22 33", "username": "sanobar",
        })
        self.assertEqual(javob.status_code, 302)
        self.operator.refresh_from_db()
        self.assertEqual(self.operator.username, "sanobar")
        self.assertEqual(self.operator.toliq_ism, "Rustamova Sanobar")

    def test_ism_ozgarsa_xodim_kartochkasi_ham_yangilanadi(self):
        xodim = Xodim.objects.create(ism="Sanjar", familiya="Rustamov",
                                     oylik_maosh=Decimal(0),
                                     foydalanuvchi=self.operator)
        self.client.post(reverse("accounts:shaxsiy"), {
            "amal": "malumot", "last_name": "Rustamova", "first_name": "Sanobar",
            "telefon": "+998 90 111 22 33", "username": "operator1",
        })
        xodim.refresh_from_db()
        self.assertEqual(xodim.toliq_ism, "Rustamova Sanobar")
        self.assertEqual(xodim.telefon, "+998 90 111 22 33")

    def test_band_login_qabul_qilinmaydi(self):
        self.client.post(reverse("accounts:shaxsiy"), {
            "amal": "malumot", "last_name": "R", "first_name": "S",
            "telefon": "", "username": "admin1",
        })
        self.operator.refresh_from_db()
        self.assertEqual(self.operator.username, "operator1")

    def test_oz_parolini_ozgartiradi_va_sessiya_uzilmaydi(self):
        javob = self.client.post(reverse("accounts:shaxsiy"), {
            "amal": "parol", "old_password": "parol12345",
            "new_password1": "yangi999", "new_password2": "yangi999",
        })
        self.assertEqual(javob.status_code, 302)
        self.operator.refresh_from_db()
        self.assertTrue(self.operator.check_password("yangi999"))
        self.assertEqual(self.client.get(reverse("accounts:shaxsiy")).status_code, 200)

    def test_notogri_joriy_parol_bilan_ozgarmaydi(self):
        self.client.post(reverse("accounts:shaxsiy"), {
            "amal": "parol", "old_password": "xato",
            "new_password1": "yangi999", "new_password2": "yangi999",
        })
        self.operator.refresh_from_db()
        self.assertTrue(self.operator.check_password("parol12345"))

    def test_qisqa_parol_qabul_qilinmaydi(self):
        self.client.post(reverse("accounts:shaxsiy"), {
            "amal": "parol", "old_password": "parol12345",
            "new_password1": "abc", "new_password2": "abc",
        })
        self.operator.refresh_from_db()
        self.assertTrue(self.operator.check_password("parol12345"))


class ChiqishTest(TestCase):
    """Yon menyudagi "Chiqish" tugmasi ishlashi kerak (Django 5+ da POST talab qilinadi)."""

    def setUp(self):
        self.admin = foydalanuvchi("admin1", Foydalanuvchi.Rol.ADMIN)
        self.client.login(username="admin1", password="parol12345")

    def test_yon_menyuda_chiqish_post_forma(self):
        html = self.client.get(reverse("dashboard:bosh")).content.decode()
        self.assertIn('action="/chiqish/"', html)
        self.assertIn('class="chiqish-forma"', html)

    def test_post_bilan_chiqadi(self):
        javob = self.client.post(reverse("accounts:chiqish"))
        self.assertEqual(javob.status_code, 302)
        keyingi = self.client.get(reverse("dashboard:bosh"))
        self.assertEqual(keyingi.status_code, 302)   # endi kirish sahifasiga yuboradi


class KeshTest(TestCase):
    """CSS/JS manzilida versiya bo'lsin - yangilangandan keyin brauzer eskisini olmasin."""

    def setUp(self):
        self.admin = foydalanuvchi("admin1", Foydalanuvchi.Rol.ADMIN)
        self.client.login(username="admin1", password="parol12345")

    def test_statik_fayllarda_versiya_bor(self):
        from django.conf import settings

        html = self.client.get(reverse("dashboard:bosh")).content.decode()
        self.assertIn(f"app.css?v={settings.SAYT_VERSIYA}", html)
        self.assertIn(f"app.js?v={settings.SAYT_VERSIYA}", html)


class BoshlangichTest(TestCase):
    def test_boshlangich_admin_hisobini_ochadi(self):
        from io import StringIO

        from django.core.management import call_command

        call_command("boshlangich", stdout=StringIO())
        admin = Foydalanuvchi.objects.get(username="admin")
        self.assertTrue(admin.check_password("admin"))
        self.assertEqual(admin.rol, Foydalanuvchi.Rol.ADMIN)
        self.assertTrue(admin.saytga_kira_oladi)

    def test_boshlangich_mavjud_hisobga_tegmaydi(self):
        from io import StringIO

        from django.core.management import call_command

        foydalanuvchi("admin", Foydalanuvchi.Rol.ADMIN, parol="mening_parolim")
        call_command("boshlangich", stdout=StringIO())
        admin = Foydalanuvchi.objects.get(username="admin")
        self.assertTrue(admin.check_password("mening_parolim"))
