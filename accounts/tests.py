"""Shaxsiy sahifa va foydalanuvchi boshqaruvi testlari."""
from django.test import TestCase
from django.urls import reverse

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

    def test_operator_boshqalar_royxatini_kormaydi(self):
        javob = self.client.get(reverse("accounts:shaxsiy"))
        self.assertNotContains(javob, "Boshqa foydalanuvchilar")

    def test_admin_boshqalar_royxatini_koradi(self):
        self.client.login(username="admin1", password="parol12345")
        javob = self.client.get(reverse("accounts:shaxsiy"))
        self.assertContains(javob, "Boshqa foydalanuvchilar")
        self.assertContains(javob, "operator1")

    def test_oz_ismini_va_loginini_ozgartiradi(self):
        javob = self.client.post(reverse("accounts:shaxsiy"), {
            "amal": "malumot", "last_name": "Rustamova", "first_name": "Sanobar",
            "telefon": "+998 90 111 22 33", "username": "sanobar",
        })
        self.assertEqual(javob.status_code, 302)
        self.operator.refresh_from_db()
        self.assertEqual(self.operator.username, "sanobar")
        self.assertEqual(self.operator.toliq_ism, "Rustamova Sanobar")

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
        # sessiya uzilmagan - sahifa hali ochiladi
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


class FoydalanuvchiBoshqaruviTest(TestCase):
    def setUp(self):
        self.admin = foydalanuvchi("admin1", Foydalanuvchi.Rol.ADMIN)
        self.operator = foydalanuvchi("operator1")
        self.client.login(username="admin1", password="parol12345")

    def test_admin_yangi_foydalanuvchi_qoshadi(self):
        javob = self.client.post(reverse("accounts:foydalanuvchi_yangi"), {
            "last_name": "Ahmedova", "first_name": "Nilufar", "telefon": "",
            "username": "nilufar", "rol": Foydalanuvchi.Rol.OPERATOR,
            "saytga_kira_oladi": "on", "parol1": "kurs2026", "parol2": "kurs2026",
        })
        self.assertEqual(javob.status_code, 302)
        yangi = Foydalanuvchi.objects.get(username="nilufar")
        self.assertTrue(yangi.check_password("kurs2026"))
        self.assertEqual(yangi.toliq_ism, "Ahmedova Nilufar")

    def test_admin_boshqaning_ismi_va_parolini_ozgartiradi(self):
        javob = self.client.post(
            reverse("accounts:foydalanuvchi_tahrir", args=[self.operator.pk]), {
                "last_name": "Rustamov", "first_name": "Sanjar", "telefon": "",
                "username": "operator1", "rol": Foydalanuvchi.Rol.OPERATOR,
                "saytga_kira_oladi": "on", "parol1": "yangi777", "parol2": "yangi777",
            })
        self.assertEqual(javob.status_code, 302)
        self.operator.refresh_from_db()
        self.assertTrue(self.operator.check_password("yangi777"))
        self.assertEqual(self.operator.toliq_ism, "Rustamov Sanjar")

    def test_parol_bosh_qoldirilsa_ozgarmaydi(self):
        self.client.post(
            reverse("accounts:foydalanuvchi_tahrir", args=[self.operator.pk]), {
                "last_name": "Rustamov", "first_name": "Sanjar", "telefon": "",
                "username": "operator1", "rol": Foydalanuvchi.Rol.OPERATOR,
                "saytga_kira_oladi": "on", "parol1": "", "parol2": "",
            })
        self.operator.refresh_from_db()
        self.assertTrue(self.operator.check_password("parol12345"))

    def test_admin_ozini_ochira_olmaydi(self):
        self.client.post(reverse("accounts:foydalanuvchi_ochirish", args=[self.admin.pk]))
        self.assertTrue(Foydalanuvchi.objects.filter(pk=self.admin.pk).exists())

    def test_admin_boshqani_ochiradi(self):
        self.client.post(reverse("accounts:foydalanuvchi_ochirish", args=[self.operator.pk]))
        self.assertFalse(Foydalanuvchi.objects.filter(pk=self.operator.pk).exists())

    def test_operator_boshqani_tahrirlay_olmaydi(self):
        self.client.login(username="operator1", password="parol12345")
        javob = self.client.get(
            reverse("accounts:foydalanuvchi_tahrir", args=[self.admin.pk]))
        self.assertEqual(javob.status_code, 302)

    def test_admin_ozini_tahrirlaganda_shaxsiy_sahifaga_yonaltiriladi(self):
        javob = self.client.get(
            reverse("accounts:foydalanuvchi_tahrir", args=[self.admin.pk]))
        self.assertRedirects(javob, reverse("accounts:shaxsiy"))


class SuperuserHimoyasiTest(TestCase):
    """Sayt admini Django admin hisobiga tegmasligi kerak."""

    def setUp(self):
        self.admin = foydalanuvchi("admin1", Foydalanuvchi.Rol.ADMIN)
        self.texnik = Foydalanuvchi.objects.create_superuser(
            username="texnik", password="parol12345")
        self.texnik.saytga_kira_oladi = False
        self.texnik.save(update_fields=["saytga_kira_oladi"])
        self.client.login(username="admin1", password="parol12345")

    def test_royxatda_korinmaydi(self):
        javob = self.client.get(reverse("accounts:shaxsiy"))
        self.assertNotContains(javob, "texnik")

    def test_tahrirlab_bolmaydi(self):
        javob = self.client.get(
            reverse("accounts:foydalanuvchi_tahrir", args=[self.texnik.pk]))
        self.assertRedirects(javob, reverse("accounts:shaxsiy"))

    def test_ochirib_bolmaydi(self):
        self.client.post(reverse("accounts:foydalanuvchi_ochirish", args=[self.texnik.pk]))
        self.assertTrue(Foydalanuvchi.objects.filter(pk=self.texnik.pk).exists())


class BoshlangichTest(TestCase):
    def test_boshlangich_admin_hisobini_ochadi(self):
        from io import StringIO

        from django.core.management import call_command

        chiqish = StringIO()
        call_command("boshlangich", stdout=chiqish)
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
