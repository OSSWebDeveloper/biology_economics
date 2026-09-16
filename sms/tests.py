"""SMS moduli testlari: navbat, qurilma ulash, taqsimlash, qayta urinish."""
import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from payments.models import Tranzaksiya
from students.models import Arxiv, Oquvchi

from . import services, sozlamalar
from .models import Bildirishnoma, Qurilma, SimKarta, SmsXabar, UlanishKodi

# Sentabr tugagan, 1-oktabrda eslatma tayyorlanadi
OKTABR = date(2025, 10, 1)

YOQ = dict(SMS_ESLATMA_YOQILGAN=True)
OCHIQ = dict(SMS_ESLATMA_YOQILGAN=False)

Foydalanuvchi = get_user_model()


def oquvchi_yarat(**qoshimcha):
    malumot = dict(
        ism="Aziz", familiya="Karimov",
        ota_telefon="+998901112233", ona_telefon="901112244",
        oylik_toluv=Decimal("450000"), boshlangan_sana=date(2025, 9, 1),
    )
    malumot.update(qoshimcha)
    return Oquvchi.objects.create(**malumot)


def qurilma_yarat(nomi="Telefon", onlayn=True, simlar=0, **qoshimcha):
    qurilma = Qurilma.objects.create(
        qurilma_id=f"id-{nomi}",
        nomi=nomi,
        kalit=Qurilma.kalit_yarat(),
        oxirgi_aloqa=timezone.now() if onlayn else timezone.now() - timedelta(hours=5),
        **qoshimcha,
    )
    for i in range(simlar):
        SimKarta.objects.create(qurilma=qurilma, sim_id=i + 1,
                                nomi=f"SIM {i + 1}", slot=i)
    return qurilma


class RaqamTest(TestCase):
    def test_turli_korinishlar(self):
        kutilgan = "+998901112233"
        for raqam in ("901112233", "+998901112233", "998901112233",
                      "(90) 111-22-33", "8901112233", "+998 90 111 22 33"):
            with self.subTest(raqam=raqam):
                self.assertEqual(services.raqamni_tozala(raqam), kutilgan)

    def test_notogri_raqam_tushib_qoladi(self):
        for raqam in ("", "   ", "123", "90111223", "abc"):
            with self.subTest(raqam=raqam):
                self.assertEqual(services.raqamni_tozala(raqam), "")


class MatnTest(TestCase):
    def test_ism_va_summa_matnda(self):
        oquvchi = oquvchi_yarat()
        matn = services.xabar_matni(oquvchi, Decimal("450000"), davr=OKTABR)
        self.assertIn("Karimov Aziz", matn)
        self.assertIn("450 000", matn)

    def test_bitta_sms_ga_sigadi(self):
        oquvchi = oquvchi_yarat(familiya="Abdurahmonov", ism="Shohruhmirzo")
        matn = services.xabar_matni(oquvchi, Decimal("1250000"), davr=OKTABR)
        self.assertLessEqual(len(matn), 160, f"Matn uzun: {len(matn)} belgi")
        self.assertEqual(services.sms_bolaklari(matn), 1)


@override_settings(**YOQ)
class NavbatTest(TestCase):
    def test_ikkalasiga(self):
        oquvchi = oquvchi_yarat()
        with override_settings(SMS_KIMGA="ikkalasi"):
            soni = services.eslatmalarni_navbatga_qoy(OKTABR)
        self.assertEqual(soni, 2)
        self.assertEqual(
            set(SmsXabar.objects.values_list("qabul_qiluvchi", flat=True)),
            {"ota", "ona"},
        )
        self.assertEqual(SmsXabar.objects.get(qabul_qiluvchi="ona").telefon,
                         "+998901112244")
        self.assertEqual(oquvchi.sms_xabarlar.count(), 2)

    def test_navbatdagi_xabar_hali_qurilmasiz(self):
        oquvchi_yarat()
        services.eslatmalarni_navbatga_qoy(OKTABR)
        for xabar in SmsXabar.objects.all():
            self.assertEqual(xabar.holat, SmsXabar.Holat.NAVBATDA)
            self.assertIsNone(xabar.qurilma_id)

    def test_faqat_otaga(self):
        oquvchi_yarat()
        with override_settings(SMS_KIMGA="ota"):
            services.eslatmalarni_navbatga_qoy(OKTABR)
        self.assertEqual(list(SmsXabar.objects.values_list("qabul_qiluvchi", flat=True)),
                         ["ota"])

    def test_faqat_onaga(self):
        oquvchi_yarat()
        with override_settings(SMS_KIMGA="ona"):
            services.eslatmalarni_navbatga_qoy(OKTABR)
        self.assertEqual(list(SmsXabar.objects.values_list("qabul_qiluvchi", flat=True)),
                         ["ona"])

    def test_raqami_yoq_ota_tushib_qoladi(self):
        oquvchi_yarat(ota_telefon="")
        services.eslatmalarni_navbatga_qoy(OKTABR)
        self.assertEqual(list(SmsXabar.objects.values_list("qabul_qiluvchi", flat=True)),
                         ["ona"])

    def test_qarzi_yoqqa_yozilmaydi(self):
        oquvchi = oquvchi_yarat()
        services.barcha_hisoblarni_yangila(sanagacha=OKTABR)
        Tranzaksiya.objects.create(oquvchi=oquvchi, tur=Tranzaksiya.Tur.TOLOV,
                                   summa=Decimal("450000"), sana=OKTABR)
        self.assertEqual(services.eslatmalarni_navbatga_qoy(OKTABR), 0)

    def test_chiqarilgan_va_arxivlanganga_yozilmaydi(self):
        chiqarilgan = oquvchi_yarat(familiya="Chiqarilgan")
        chiqarilgan.faol = False
        chiqarilgan.save()

        arxivda = oquvchi_yarat(familiya="Arxivda")
        Arxiv.objects.create(oquvchi=arxivda, sabab=Arxiv.Sabab.SERTIFIKAT,
                             sana=date(2025, 9, 30))

        oquvchi_yarat(familiya="Oddiy")
        services.eslatmalarni_navbatga_qoy(OKTABR)
        self.assertEqual(
            set(SmsXabar.objects.values_list("oquvchi__familiya", flat=True)),
            {"Oddiy"},
        )

    def test_takrorlanmaydi(self):
        oquvchi_yarat()
        self.assertEqual(services.eslatmalarni_navbatga_qoy(OKTABR), 2)
        self.assertEqual(services.eslatmalarni_navbatga_qoy(OKTABR), 0)
        self.assertEqual(SmsXabar.objects.count(), 2)

    def test_faqat_belgilangan_kunlarda(self):
        oquvchi_yarat()
        self.assertEqual(services.eslatmalarni_navbatga_qoy(date(2025, 10, 20)), 0)
        self.assertEqual(services.eslatmalarni_navbatga_qoy(date(2025, 10, 8)), 2)

    @override_settings(SMS_TEST_RAQAM="+998900000000")
    def test_sinov_raqami(self):
        oquvchi_yarat()
        services.eslatmalarni_navbatga_qoy(OKTABR)
        self.assertEqual(set(SmsXabar.objects.values_list("telefon", flat=True)),
                         {"+998900000000"})

    @override_settings(SMS_ENG_KAM_QARZ=1000000)
    def test_kichik_qarzga_yozilmaydi(self):
        oquvchi_yarat()
        self.assertEqual(services.eslatmalarni_navbatga_qoy(OKTABR), 0)


@override_settings(**YOQ)
class UlanishTest(TestCase):
    def malumot(self, kod, qurilma_id="telefon-1"):
        return {
            "kod": kod,
            "qurilma_id": qurilma_id,
            "nomi": "Samsung Galaxy A51",
            "ishlab_chiqaruvchi": "samsung",
            "model": "SM-A515F",
            "android": "13",
            "ilova_versiya": "1.0.0",
            "simlar": [
                {"id": 1, "nomi": "Beeline", "raqam": "901112233", "slot": 0},
                {"id": 2, "nomi": "Ucell", "raqam": "931112233", "slot": 1},
            ],
        }

    def test_kod_12_xonali(self):
        kod = UlanishKodi.yarat()
        self.assertEqual(len(kod.kod), 12)
        self.assertTrue(kod.kod.isdigit())
        self.assertTrue(kod.yaroqli)
        self.assertEqual(kod.korinish.count(" "), 2)

    def test_ulanish(self):
        kod = UlanishKodi.yarat()
        qurilma, kalit = services.qurilmani_ulash(kod.kod, self.malumot(kod.kod))

        self.assertEqual(qurilma.nomi, "Samsung Galaxy A51")
        self.assertEqual(qurilma.android, "13")
        self.assertEqual(qurilma.simlar.count(), 2)
        self.assertEqual(qurilma.kalit, kalit)
        self.assertTrue(qurilma.onlayn)

        kod.refresh_from_db()
        self.assertIsNotNone(kod.ishlatilgan)
        self.assertFalse(kod.yaroqli)
        self.assertTrue(
            Bildirishnoma.objects.filter(turi=Bildirishnoma.Turi.ULANDI).exists()
        )

    def test_kod_ikki_marta_ishlamaydi(self):
        kod = UlanishKodi.yarat()
        services.qurilmani_ulash(kod.kod, self.malumot(kod.kod))
        with self.assertRaises(services.UlanishXatosi):
            services.qurilmani_ulash(kod.kod, self.malumot(kod.kod, "telefon-2"))

    def test_notogri_kod(self):
        with self.assertRaises(services.UlanishXatosi):
            services.qurilmani_ulash("123", {"qurilma_id": "x"})
        with self.assertRaises(services.UlanishXatosi):
            services.qurilmani_ulash("999999999999", {"qurilma_id": "x"})

    def test_muddati_otgan_kod(self):
        kod = UlanishKodi.yarat()
        kod.amal_qiladi = timezone.now() - timedelta(minutes=1)
        kod.save()
        with self.assertRaises(services.UlanishXatosi):
            services.qurilmani_ulash(kod.kod, self.malumot(kod.kod))

    def test_qayta_ulanishda_kalit_yangilanadi(self):
        kod1 = UlanishKodi.yarat()
        qurilma1, kalit1 = services.qurilmani_ulash(kod1.kod, self.malumot(kod1.kod))

        kod2 = UlanishKodi.yarat()
        qurilma2, kalit2 = services.qurilmani_ulash(kod2.kod, self.malumot(kod2.kod))

        self.assertEqual(qurilma1.pk, qurilma2.pk)     # o'sha qurilma
        self.assertNotEqual(kalit1, kalit2)            # kalit yangilandi
        self.assertEqual(Qurilma.objects.count(), 1)

    def test_sim_royxati_yangilanadi(self):
        kod = UlanishKodi.yarat()
        qurilma, _ = services.qurilmani_ulash(kod.kod, self.malumot(kod.kod))
        # bitta SIM olib tashlandi
        services.simlarni_yangila(qurilma, [{"id": 1, "nomi": "Beeline"}])
        self.assertEqual(qurilma.simlar.count(), 1)


@override_settings(**YOQ)
class TaqsimlashTest(TestCase):
    def setUp(self):
        for i in range(5):
            oquvchi_yarat(familiya=f"Oquvchi{i}", ona_telefon="")   # har biriga 1 ta
        services.eslatmalarni_navbatga_qoy(OKTABR)
        self.assertEqual(SmsXabar.objects.count(), 5)

    def test_bitta_qurilmaga_hammasi(self):
        qurilma = qurilma_yarat("Telefon A")
        natija = services.taqsimla(services.kanallar_royxati(None, [qurilma.pk]))
        self.assertEqual(natija["jami"], 5)
        self.assertEqual(SmsXabar.objects.filter(qurilma=qurilma).count(), 5)
        self.assertEqual(
            set(SmsXabar.objects.values_list("holat", flat=True)),
            {SmsXabar.Holat.BERILDI},
        )

    def test_ikki_qurilmaga_teng_bolinadi(self):
        a = qurilma_yarat("Telefon A")
        b = qurilma_yarat("Telefon B")
        services.taqsimla(services.kanallar_royxati(None, [a.pk, b.pk]))
        self.assertEqual(SmsXabar.objects.filter(qurilma=a).count(), 3)
        self.assertEqual(SmsXabar.objects.filter(qurilma=b).count(), 2)

    def test_sim_kanallari(self):
        qurilma = qurilma_yarat("Ikki simli", simlar=2)
        sim1, sim2 = qurilma.simlar.order_by("slot")
        services.taqsimla(services.kanallar_royxati([sim1.pk, sim2.pk], [qurilma.pk]))
        self.assertEqual(SmsXabar.objects.filter(sim=sim1).count(), 3)
        self.assertEqual(SmsXabar.objects.filter(sim=sim2).count(), 2)
        # qurilma ikki marta hisoblanmasligi kerak
        self.assertEqual(SmsXabar.objects.filter(sim__isnull=True).count(), 0)

    def test_qurilmasiz_taqsimlanmaydi(self):
        natija = services.taqsimla([])
        self.assertEqual(natija["jami"], 0)
        self.assertEqual(
            SmsXabar.objects.filter(holat=SmsXabar.Holat.NAVBATDA).count(), 5)

    def test_oflayn_qurilmadan_qaytarib_olinadi(self):
        qurilma = qurilma_yarat("Oflayn", onlayn=False)
        services.taqsimla(services.kanallar_royxati(None, [qurilma.pk]))
        SmsXabar.objects.update(berilgan=timezone.now() - timedelta(hours=4))

        qaytdi = services.berilganlarni_bosat(daqiqa=120)
        self.assertEqual(qaytdi, 5)
        self.assertEqual(
            SmsXabar.objects.filter(holat=SmsXabar.Holat.NAVBATDA,
                                    qurilma__isnull=True).count(), 5)


@override_settings(**YOQ)
class QurilmaNavbatiTest(TestCase):
    def setUp(self):
        oquvchi_yarat()
        services.eslatmalarni_navbatga_qoy(OKTABR)
        self.a = qurilma_yarat("Telefon A")
        self.b = qurilma_yarat("Telefon B")

    def test_faqat_ozining_xabarlarini_oladi(self):
        services.taqsimla(services.kanallar_royxati(None, [self.a.pk]))
        self.assertEqual(len(services.qurilma_navbati(self.a)), 2)
        self.assertEqual(len(services.qurilma_navbati(self.b)), 0)

    def test_olingandan_keyin_qayta_berilmaydi(self):
        services.taqsimla(services.kanallar_royxati(None, [self.a.pk]))
        self.assertEqual(len(services.qurilma_navbati(self.a)), 2)
        self.assertEqual(len(services.qurilma_navbati(self.a)), 0)

    def test_natija_qabul_qilinadi(self):
        services.taqsimla(services.kanallar_royxati(None, [self.a.pk]))
        xabarlar = services.qurilma_navbati(self.a)

        services.holatni_belgila(xabarlar[0].pk, SmsXabar.Holat.JONATILDI,
                                 qurilma=self.a)
        xabarlar[0].refresh_from_db()
        self.assertEqual(xabarlar[0].holat, SmsXabar.Holat.JONATILDI)
        self.assertIsNotNone(xabarlar[0].jonatilgan)

    def test_boshqa_qurilma_natija_qaytara_olmaydi(self):
        services.taqsimla(services.kanallar_royxati(None, [self.a.pk]))
        xabarlar = services.qurilma_navbati(self.a)
        natija = services.holatni_belgila(
            xabarlar[0].pk, SmsXabar.Holat.JONATILDI, qurilma=self.b)
        self.assertFalse(natija)

    def test_urinishlar_tugasa_xato(self):
        services.taqsimla(services.kanallar_royxati(None, [self.a.pk]))
        for _ in range(sozlamalar.urinishlar_chegarasi()):
            for xabar in services.qurilma_navbati(self.a):
                services.holatni_belgila(xabar.pk, SmsXabar.Holat.XATO,
                                         "aloqa yo'q", self.a)
        self.assertEqual(
            set(SmsXabar.objects.values_list("holat", flat=True)), {SmsXabar.Holat.XATO})
        self.assertTrue(
            Bildirishnoma.objects.filter(turi=Bildirishnoma.Turi.XATO).exists())


@override_settings(**YOQ)
class QaytaUrinishTest(TestCase):
    def setUp(self):
        oquvchi_yarat()
        services.eslatmalarni_navbatga_qoy(OKTABR)

    def _xato_qil(self, qurilma):
        services.taqsimla(services.kanallar_royxati(None, [qurilma.pk]))
        for _ in range(sozlamalar.urinishlar_chegarasi()):
            for xabar in services.qurilma_navbati(qurilma):
                services.holatni_belgila(xabar.pk, SmsXabar.Holat.XATO, "xato", qurilma)

    def test_onlayn_qurilmada_qoladi(self):
        qurilma = qurilma_yarat("Onlayn")
        self._xato_qil(qurilma)
        xabar = SmsXabar.objects.first()
        holat = services.qayta_urin(xabar)
        self.assertEqual(holat, SmsXabar.Holat.BERILDI)
        xabar.refresh_from_db()
        self.assertEqual(xabar.qurilma, qurilma)
        self.assertEqual(xabar.urinishlar, 0)

    def test_oflayn_bolsa_navbatga_qaytadi(self):
        qurilma = qurilma_yarat("Oflayn", onlayn=False)
        self._xato_qil(qurilma)
        xabar = SmsXabar.objects.first()
        holat = services.qayta_urin(xabar)
        self.assertEqual(holat, SmsXabar.Holat.NAVBATDA)
        xabar.refresh_from_db()
        self.assertIsNone(xabar.qurilma_id)

    def test_hammasini_qayta_urinish(self):
        qurilma = qurilma_yarat("Telefon")
        self._xato_qil(qurilma)
        self.assertEqual(services.hammasini_qayta_urin(), 2)
        self.assertEqual(SmsXabar.objects.filter(holat=SmsXabar.Holat.XATO).count(), 0)


@override_settings(**YOQ)
class ApiTest(TestCase):
    def setUp(self):
        oquvchi_yarat()
        services.eslatmalarni_navbatga_qoy(OKTABR)
        self.qurilma = qurilma_yarat("Telefon A", simlar=2)

    def sarlavha(self, kalit=None):
        return {"x-sms-kalit": kalit or self.qurilma.kalit}

    def test_ulanish_api(self):
        kod = UlanishKodi.yarat()
        javob = self.client.post(
            reverse("sms_api:ulan"),
            data=json.dumps({
                "kod": kod.kod, "qurilma_id": "yangi-telefon", "nomi": "Redmi 9",
                "android": "11", "ilova_versiya": "1.0.0",
                "simlar": [{"id": 5, "nomi": "Mobiuz", "raqam": "944445566"}],
            }),
            content_type="application/json",
        )
        self.assertEqual(javob.status_code, 200)
        malumot = javob.json()
        self.assertTrue(malumot["ok"])
        self.assertTrue(malumot["kalit"])
        self.assertEqual(malumot["simlar"], 1)
        self.assertTrue(Qurilma.objects.filter(qurilma_id="yangi-telefon").exists())

    def test_notogri_kod_bilan_ulanmaydi(self):
        javob = self.client.post(
            reverse("sms_api:ulan"),
            data=json.dumps({"kod": "000000000000", "qurilma_id": "x"}),
            content_type="application/json",
        )
        self.assertEqual(javob.status_code, 400)
        self.assertFalse(javob.json()["ok"])

    def test_kalitsiz_kirib_bolmaydi(self):
        self.assertEqual(self.client.get(reverse("sms_api:navbat")).status_code, 403)
        self.assertEqual(
            self.client.get(reverse("sms_api:navbat"),
                            headers=self.sarlavha("boshqa")).status_code, 403)

    def test_tekshir_aloqani_yangilaydi(self):
        self.qurilma.oxirgi_aloqa = timezone.now() - timedelta(hours=3)
        self.qurilma.save()
        javob = self.client.get(reverse("sms_api:tekshir") + "?batareya=77&versiya=1.0.0",
                                headers=self.sarlavha())
        self.assertEqual(javob.status_code, 200)
        self.qurilma.refresh_from_db()
        self.assertTrue(self.qurilma.onlayn)
        self.assertEqual(self.qurilma.batareya, 77)

    def test_navbat_va_holat(self):
        sim = self.qurilma.simlar.first()
        services.taqsimla([(self.qurilma, sim)])

        javob = self.client.get(reverse("sms_api:navbat"), headers=self.sarlavha())
        malumot = javob.json()
        self.assertEqual(malumot["soni"], 2)
        self.assertEqual(malumot["xabarlar"][0]["sim"], sim.sim_id)

        javob2 = self.client.post(
            reverse("sms_api:holat"),
            data=json.dumps({"natijalar": [
                {"id": malumot["xabarlar"][0]["id"], "holat": "jonatildi"},
                {"id": malumot["xabarlar"][1]["id"], "holat": "xato", "xato": "tarmoq"},
            ]}),
            content_type="application/json", headers=self.sarlavha(),
        )
        self.assertEqual(javob2.json()["qabul"], 2)
        self.assertEqual(
            SmsXabar.objects.filter(holat=SmsXabar.Holat.JONATILDI).count(), 1)

    def test_simlarni_yangilash_api(self):
        javob = self.client.post(
            reverse("sms_api:simlar"),
            data=json.dumps({"simlar": [{"id": 9, "nomi": "Yangi SIM"}]}),
            content_type="application/json", headers=self.sarlavha(),
        )
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(self.qurilma.simlar.count(), 1)

    def test_ochirilgan_qurilma_kira_olmaydi(self):
        self.qurilma.faol = False
        self.qurilma.save()
        self.assertEqual(
            self.client.get(reverse("sms_api:navbat"),
                            headers=self.sarlavha()).status_code, 403)

    def test_buzuq_json(self):
        javob = self.client.post(reverse("sms_api:holat"), data="{buzuq",
                                 content_type="application/json",
                                 headers=self.sarlavha())
        self.assertEqual(javob.status_code, 400)


class OchiqHolatTest(TestCase):
    """Modul o'chiq bo'lsa hech qayerda ko'rinmaydi."""

    def setUp(self):
        self.admin = Foydalanuvchi.objects.create_user(
            username="admin", password="parol", rol="admin")

    @override_settings(**OCHIQ)
    def test_navbat_tayyorlanmaydi(self):
        oquvchi_yarat()
        self.assertEqual(services.eslatmalarni_navbatga_qoy(OKTABR), 0)
        self.assertEqual(services.avtomatik_tekshir(), 0)
        self.assertEqual(SmsXabar.objects.count(), 0)

    @override_settings(**OCHIQ)
    def test_api_topilmaydi(self):
        self.assertEqual(self.client.get(reverse("sms_api:navbat")).status_code, 404)
        self.assertEqual(self.client.post(reverse("sms_api:ulan")).status_code, 404)

    @override_settings(**OCHIQ)
    def test_sahifalar_topilmaydi(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("sms:bosh")).status_code, 404)
        self.assertEqual(self.client.get(reverse("sms:xabarlar")).status_code, 404)

    @override_settings(**OCHIQ)
    def test_menyuda_korinmaydi(self):
        self.client.force_login(self.admin)
        javob = self.client.get(reverse("dashboard:bosh"))
        self.assertNotContains(javob, "Xabarnoma")

    @override_settings(**YOQ)
    def test_yoqilganda_menyuda_bor(self):
        self.client.force_login(self.admin)
        javob = self.client.get(reverse("dashboard:bosh"))
        self.assertContains(javob, "Xabarnoma")


@override_settings(**YOQ)
class SahifaTest(TestCase):
    def setUp(self):
        self.admin = Foydalanuvchi.objects.create_user(
            username="admin", password="parol", rol="admin")
        self.oqituvchi = Foydalanuvchi.objects.create_user(
            username="domla", password="parol", rol="oqituvchi")
        self.client.force_login(self.admin)

    def test_bosh_sahifa(self):
        qurilma_yarat("Telefon A", simlar=2)
        javob = self.client.get(reverse("sms:bosh"))
        self.assertEqual(javob.status_code, 200)
        self.assertContains(javob, "Telefon A")

    def test_oqituvchi_kira_olmaydi(self):
        self.client.force_login(self.oqituvchi)
        javob = self.client.get(reverse("sms:bosh"))
        self.assertEqual(javob.status_code, 302)

    def test_kod_yaratish(self):
        javob = self.client.post(reverse("sms:kod_yarat"))
        self.assertEqual(javob.status_code, 302)
        self.assertEqual(UlanishKodi.objects.count(), 1)
        self.assertEqual(len(UlanishKodi.objects.first().kod), 12)

    def test_yuborish(self):
        oquvchi_yarat()
        services.eslatmalarni_navbatga_qoy(OKTABR)
        qurilma = qurilma_yarat("Telefon A")

        javob = self.client.post(reverse("sms:yuborish"), {"qurilma": [str(qurilma.pk)]})
        self.assertEqual(javob.status_code, 302)
        self.assertEqual(SmsXabar.objects.filter(qurilma=qurilma).count(), 2)

    def test_qurilmasiz_yuborish_xato_beradi(self):
        oquvchi_yarat()
        services.eslatmalarni_navbatga_qoy(OKTABR)
        javob = self.client.post(reverse("sms:yuborish"), {}, follow=True)
        self.assertContains(javob, "qurilma tanlanmadi")

    def test_qurilmani_ochirish_xabarlarni_qaytaradi(self):
        oquvchi_yarat()
        services.eslatmalarni_navbatga_qoy(OKTABR)
        qurilma = qurilma_yarat("Telefon A")
        services.taqsimla(services.kanallar_royxati(None, [qurilma.pk]))

        self.client.post(reverse("sms:qurilma_ochir", args=[qurilma.pk]))
        qurilma.refresh_from_db()
        self.assertFalse(qurilma.faol)
        self.assertEqual(
            SmsXabar.objects.filter(holat=SmsXabar.Holat.NAVBATDA).count(), 2)

    def test_qurilmani_uzish(self):
        qurilma = qurilma_yarat("Telefon A")
        self.client.post(reverse("sms:qurilma_uzish", args=[qurilma.pk]))
        self.assertEqual(Qurilma.objects.count(), 0)

    def test_xatolar_sahifasi_va_qayta_urinish(self):
        oquvchi_yarat()
        services.eslatmalarni_navbatga_qoy(OKTABR)
        qurilma = qurilma_yarat("Telefon A")
        services.taqsimla(services.kanallar_royxati(None, [qurilma.pk]))
        for _ in range(sozlamalar.urinishlar_chegarasi()):
            for xabar in services.qurilma_navbati(qurilma):
                services.holatni_belgila(xabar.pk, SmsXabar.Holat.XATO, "tarmoq yo'q",
                                         qurilma)

        javob = self.client.get(reverse("sms:xatolar"))
        self.assertEqual(javob.status_code, 200)
        self.assertContains(javob, "tarmoq yo")

        self.client.post(reverse("sms:hammasini_qayta_urin"))
        self.assertEqual(SmsXabar.objects.filter(holat=SmsXabar.Holat.XATO).count(), 0)

    def test_holat_json(self):
        qurilma_yarat("Telefon A")
        javob = self.client.get(reverse("sms:holat_json"))
        self.assertEqual(javob.status_code, 200)
        malumot = javob.json()
        self.assertEqual(malumot["jami"], 1)
        self.assertEqual(malumot["onlayn"], 1)


@override_settings(**YOQ)
class RejalashtiruvchisizTest(TestCase):
    """Navbat telefon murojaat qilganda ham tayyorlanadi.

    Ochiq serverda (PythonAnywhere bepul tarifida) rejalashtirilgan vazifa
    yo'q, shuning uchun oylik navbat ilovaning davriy so'rovi bilan
    tayyorlanadi - hech kim saytni ochmasa ham.
    """

    def setUp(self):
        oquvchi_yarat()
        self.qurilma = qurilma_yarat("Telefon A", simlar=1)

    def sorov(self):
        return self.client.get(reverse("sms_api:tekshir"),
                               headers={"x-sms-kalit": self.qurilma.kalit})

    def test_tayyorlash_kunida_navbat_yoziladi(self):
        self.assertEqual(SmsXabar.objects.count(), 0)
        with override_settings(SMS_YUBORISH_KUNI=date.today().day,
                               SMS_KECHIKISH_KUNI=0):
            javob = self.sorov()
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(SmsXabar.objects.count(), 2)
        # Navbatga yozildi, lekin hali hech qaysi qurilmaga berilmadi -
        # SMS baribir admin "Yuborish" ni bosgandan keyin ketadi.
        self.assertEqual(
            SmsXabar.objects.filter(holat=SmsXabar.Holat.NAVBATDA).count(), 2)

    def test_boshqa_kunda_tegmaydi(self):
        boshqa_kun = (date.today().day % 28) + 1   # bugundan farqli kun
        with override_settings(SMS_YUBORISH_KUNI=boshqa_kun, SMS_KECHIKISH_KUNI=0):
            javob = self.sorov()
        self.assertEqual(javob.status_code, 200)
        self.assertEqual(SmsXabar.objects.count(), 0)

    def test_ikki_marta_chaqirilsa_takrorlanmaydi(self):
        with override_settings(SMS_YUBORISH_KUNI=date.today().day,
                               SMS_KECHIKISH_KUNI=0):
            self.sorov()
            self.sorov()
        self.assertEqual(SmsXabar.objects.count(), 2)
