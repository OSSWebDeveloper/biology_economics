"""Kurs to'lovlarini hisoblash qoidalarining testlari."""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from students.models import Guruh, Oquvchi

from .forms import TolovForm
from .models import Tranzaksiya, Usul
from .services import (
    balans_holati,
    barcha_hisoblarni_yangila,
    davr_summasi,
    hisoblarni_yarat,
    kunlik_narx,
    oquvchi_balansi,
    oyni_qayta_hisobla,
)

SENTABR = date(2025, 9, 1)   # 30 kunlik oy
OKTABR = date(2025, 10, 1)   # 31 kunlik oy


def oquvchi_yarat(boshlangan, oylik=600000, **qoshimcha):
    return Oquvchi.objects.create(
        ism="Ali", familiya="Valiyev", telefon="+998901234567",
        oylik_toluv=Decimal(oylik), boshlangan_sana=boshlangan, **qoshimcha,
    )


class KunlikHisobTest(TestCase):
    def test_kunlik_narx_oy_kunlariga_bolinadi(self):
        self.assertEqual(kunlik_narx(Decimal(600000), SENTABR), Decimal(20000))
        # Oktabr 31 kun -> kunlik narx boshqacha
        self.assertAlmostEqual(
            float(kunlik_narx(Decimal(620000), OKTABR)), 20000.0, places=4
        )

    def test_oy_boshidan_kelgan_toliq_oylik_tolaydi(self):
        oquvchi = oquvchi_yarat(SENTABR)
        summa, kunlar = davr_summasi(oquvchi, SENTABR)
        self.assertEqual(summa, Decimal(600000))
        self.assertEqual(kunlar, 30)

    def test_oy_ortasidan_kelgan_qolgan_kunlar_uchun_tolaydi(self):
        """15-sentabrdan kelgan o'quvchi 1-oktabrgacha - 16 kun uchun to'laydi."""
        oquvchi = oquvchi_yarat(date(2025, 9, 15))
        summa, kunlar = davr_summasi(oquvchi, SENTABR)
        self.assertEqual(kunlar, 16)
        self.assertEqual(summa, Decimal(320000))   # 20 000 * 16

    def test_keyingi_oydan_yangi_toliq_sikl_boshlanadi(self):
        oquvchi = oquvchi_yarat(date(2025, 9, 15))
        hisoblarni_yarat(oquvchi, sanagacha=date(2025, 10, 20))

        hisoblar = list(
            Tranzaksiya.objects.filter(oquvchi=oquvchi, tur=Tranzaksiya.Tur.HISOB)
            .order_by("davr")
        )
        self.assertEqual(len(hisoblar), 2)
        self.assertEqual(hisoblar[0].summa, Decimal(320000))    # 16 kunlik sentabr
        self.assertEqual(hisoblar[0].kunlar, 16)
        self.assertEqual(hisoblar[1].summa, Decimal(600000))    # to'liq oktabr
        self.assertEqual(hisoblar[1].kunlar, 31)

    def test_hisoblash_takrorlanmaydi(self):
        oquvchi = oquvchi_yarat(SENTABR)
        barcha_hisoblarni_yangila(sanagacha=date(2025, 11, 10))
        birinchi = Tranzaksiya.objects.filter(tur=Tranzaksiya.Tur.HISOB).count()
        barcha_hisoblarni_yangila(sanagacha=date(2025, 11, 10))
        self.assertEqual(
            Tranzaksiya.objects.filter(tur=Tranzaksiya.Tur.HISOB).count(), birinchi
        )
        self.assertEqual(birinchi, 3)   # sentabr, oktabr, noyabr
        self.assertEqual(oquvchi.tranzaksiyalar.count(), 3)

    def test_oylik_toluv_nol_bolsa_hisob_ochilmaydi(self):
        oquvchi = oquvchi_yarat(SENTABR, oylik=0)
        hisoblarni_yarat(oquvchi, sanagacha=date(2025, 10, 5))
        self.assertEqual(oquvchi.tranzaksiyalar.count(), 0)


class BalansTest(TestCase):
    def setUp(self):
        self.oquvchi = oquvchi_yarat(SENTABR)
        hisoblarni_yarat(self.oquvchi, sanagacha=date(2025, 9, 20))

    def test_tolovsiz_oquvchi_qarzdor(self):
        balans = oquvchi_balansi(self.oquvchi)
        self.assertEqual(balans, Decimal(-600000))
        self.assertEqual(balans_holati(balans)["kod"], "qarzdor")

    def test_toliq_tolov_qarzni_yopadi(self):
        Tranzaksiya.objects.create(
            oquvchi=self.oquvchi, tur=Tranzaksiya.Tur.TOLOV,
            summa=Decimal(600000), sana=date(2025, 9, 5), usul=Usul.NAQD,
        )
        balans = oquvchi_balansi(self.oquvchi)
        self.assertEqual(balans, Decimal(0))
        self.assertEqual(balans_holati(balans)["kod"], "toza")

    def test_ortiqcha_tolov_oldindan_tolangan_boladi(self):
        Tranzaksiya.objects.create(
            oquvchi=self.oquvchi, tur=Tranzaksiya.Tur.TOLOV,
            summa=Decimal(1000000), sana=date(2025, 9, 5), usul=Usul.PLASTIK,
            karta_raqami="8600123412341234",
        )
        balans = oquvchi_balansi(self.oquvchi)
        self.assertEqual(balans, Decimal(400000))
        holat = balans_holati(balans)
        self.assertEqual(holat["kod"], "oldindan")
        self.assertEqual(holat["summa"], Decimal(400000))

    def test_oqituvchi_qarzi_oldindan_tolovga_otadi(self):
        """O'qituvchi o'quvchidan qarz bo'lsa, u oldindan to'lov hisobiga qo'shiladi."""
        Tranzaksiya.objects.create(
            oquvchi=self.oquvchi, tur=Tranzaksiya.Tur.TOLOV,
            summa=Decimal(600000), sana=date(2025, 9, 5), usul=Usul.NAQD,
        )
        Tranzaksiya.objects.create(
            oquvchi=self.oquvchi, tur=Tranzaksiya.Tur.QARZ,
            summa=Decimal(150000), sana=date(2025, 9, 10),
            izoh="Darslar o'tkazilmadi",
        )
        balans = oquvchi_balansi(self.oquvchi)
        self.assertEqual(balans, Decimal(150000))
        self.assertEqual(balans_holati(balans)["kod"], "oldindan")

    def test_chegirma_qarzni_kamaytiradi(self):
        Tranzaksiya.objects.create(
            oquvchi=self.oquvchi, tur=Tranzaksiya.Tur.CHEGIRMA,
            summa=Decimal(100000), sana=date(2025, 9, 2),
        )
        self.assertEqual(oquvchi_balansi(self.oquvchi), Decimal(-500000))


class ChiqarishTest(TestCase):
    def test_chiqarilgan_oy_kunlab_qayta_hisoblanadi(self):
        oquvchi = oquvchi_yarat(SENTABR)
        hisoblarni_yarat(oquvchi, sanagacha=date(2025, 9, 25))
        self.assertEqual(oquvchi_balansi(oquvchi), Decimal(-600000))

        oquvchi.faol = False
        oquvchi.chiqarilgan_sana = date(2025, 9, 10)
        oquvchi.save()
        oyni_qayta_hisobla(oquvchi, SENTABR, date(2025, 9, 10))

        hisob = Tranzaksiya.objects.get(oquvchi=oquvchi, tur=Tranzaksiya.Tur.HISOB)
        self.assertEqual(hisob.kunlar, 10)
        self.assertEqual(hisob.summa, Decimal(200000))          # 20 000 * 10
        self.assertEqual(oquvchi_balansi(oquvchi), Decimal(-200000))

    def test_chiqarilgan_oquvchiga_yangi_oy_hisoblanmaydi(self):
        oquvchi = oquvchi_yarat(SENTABR, faol=False,
                                chiqarilgan_sana=date(2025, 9, 20))
        hisoblarni_yarat(oquvchi, sanagacha=date(2025, 12, 31))
        davrlar = list(
            Tranzaksiya.objects.filter(oquvchi=oquvchi, tur=Tranzaksiya.Tur.HISOB)
            .values_list("davr", flat=True)
        )
        self.assertEqual(davrlar, [SENTABR])


class GuruhTest(TestCase):
    def test_guruh_faol_oquvchilarni_sanaydi(self):
        guruh = Guruh.objects.create(nomi="9-sinf", oylik_toluv=Decimal(500000))
        oquvchi_yarat(SENTABR, guruh=guruh)
        oquvchi_yarat(SENTABR, guruh=guruh, faol=False,
                      chiqarilgan_sana=date(2025, 9, 15))
        self.assertEqual(guruh.faol_oquvchilar_soni, 1)


class PulMaydoniTest(TestCase):
    """Pul maydonlari 3 000 000 ko'rinishida ham qabul qilinishi kerak."""

    def test_bosliqli_summa_qabul_qilinadi(self):
        from students.forms import GuruhForm

        form = GuruhForm(data={"nomi": "11-sinf", "oylik_toluv": "3 000 000",
                               "faol": "on"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["oylik_toluv"], Decimal(3000000))

    def test_tolov_summasi_bosliq_bilan(self):
        oquvchi = oquvchi_yarat(SENTABR)
        form = TolovForm(data={"tur": "tolov", "summa": "1 250 000",
                               "sana": "2025-09-05", "usul": "naqd"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["summa"], Decimal(1250000))

    def test_korinishida_ajratib_chiqadi(self):
        from students.forms import GuruhForm
        from students.models import Guruh

        guruh = Guruh.objects.create(nomi="Test", oylik_toluv=Decimal(3000000))
        html = str(GuruhForm(instance=guruh)["oylik_toluv"])
        self.assertIn('value="3 000 000"', html)


class NarxMerosTest(TestCase):
    """Narx bo'sh qoldirilsa guruhdan olinadi, yozilsa o'sha narx ishlatiladi."""

    def setUp(self):
        self.guruh = Guruh.objects.create(nomi="11-sinf", oylik_toluv=Decimal(600000))

    def _oquvchi(self, **qo):
        return Oquvchi.objects.create(ism="Ali", familiya="Valiyev",
                                      telefon="+998901234567",
                                      boshlangan_sana=SENTABR, guruh=self.guruh, **qo)

    def test_bosh_qoldirilsa_guruh_narxi_olinadi(self):
        oquvchi = self._oquvchi(oylik_toluv=None)
        self.assertEqual(oquvchi.amaldagi_oylik, Decimal(600000))
        self.assertFalse(oquvchi.narxi_ozidan)
        summa, _ = davr_summasi(oquvchi, SENTABR)
        self.assertEqual(summa, Decimal(600000))

    def test_narx_yozilsa_osha_narx_ishlatiladi(self):
        oquvchi = self._oquvchi(oylik_toluv=Decimal(450000))
        self.assertEqual(oquvchi.amaldagi_oylik, Decimal(450000))
        self.assertTrue(oquvchi.narxi_ozidan)
        summa, _ = davr_summasi(oquvchi, SENTABR)
        self.assertEqual(summa, Decimal(450000))

    def test_guruh_narxi_ozgarsa_meros_olganlar_ham_ozgaradi(self):
        meros = self._oquvchi(oylik_toluv=None)
        alohida = self._oquvchi(oylik_toluv=Decimal(450000))
        self.guruh.oylik_toluv = Decimal(700000)
        self.guruh.save()
        meros.refresh_from_db(); alohida.refresh_from_db()
        self.assertEqual(meros.amaldagi_oylik, Decimal(700000))
        self.assertEqual(alohida.amaldagi_oylik, Decimal(450000))

    def test_guruhsiz_va_narxsiz_oquvchi_qabul_qilinmaydi(self):
        from students.forms import OquvchiForm

        form = OquvchiForm(data={"ism": "Ali", "familiya": "Valiyev",
                                 "telefon": "+998901234567", "ota_telefon": "",
                                 "ona_telefon": "", "guruh": "",
                                 "oylik_toluv": "", "boshlangan_sana": "2025-09-01",
                                 "izoh": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("oylik_toluv", form.errors)

    def test_guruh_bilan_narxsiz_forma_qabul_qilinadi(self):
        from students.forms import OquvchiForm

        form = OquvchiForm(data={"ism": "Ali", "familiya": "Valiyev",
                                 "telefon": "+998901234567", "ota_telefon": "",
                                 "ona_telefon": "", "guruh": str(self.guruh.pk),
                                 "oylik_toluv": "", "boshlangan_sana": "2025-09-01",
                                 "izoh": ""})
        self.assertTrue(form.is_valid(), form.errors)
        oquvchi = form.save()
        self.assertIsNone(oquvchi.oylik_toluv)
        self.assertEqual(oquvchi.amaldagi_oylik, Decimal(600000))
