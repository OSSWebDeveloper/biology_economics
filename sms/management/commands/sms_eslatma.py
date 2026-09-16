"""Oylik to'lov eslatmasi navbatini tayyorlash.

Har oyning 1-sanasida ishga tushirilishi kerak (Windows Task Scheduler):
    python manage.py sms_eslatma

DIQQAT: bu buyruq faqat NAVBAT tayyorlaydi. SMS lar admin saytdagi
"Xabarnoma -> Xabarlar" bo'limida qurilma tanlab "Yuborish" ni bosgandan
keyin ketadi.

Foydali kalitlar:
    --sinov              hech nima yozmay, nima tayyorlanishini ko'rsatadi
    --sana 2026-10-01    boshqa sanani sinab ko'rish
    --majburiy           1-sanadan tashqari kunda ham navbat tayyorlash
    --holat              navbat va qurilmalar holati
"""
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from sms import services, sozlamalar


class Command(BaseCommand):
    help = "Qarzdor o'quvchilarning ota-onasiga to'lov eslatmasini navbatga qo'yadi."

    def add_arguments(self, parser):
        parser.add_argument("--sinov", action="store_true",
                            help="Bazaga yozmaydi, faqat ro'yxatni chiqaradi.")
        parser.add_argument("--majburiy", action="store_true",
                            help="Oyning 1-sanasi bo'lmasa ham navbat tayyorlaydi.")
        parser.add_argument("--holat", action="store_true",
                            help="Navbat va qurilmalar holatini ko'rsatadi.")
        parser.add_argument("--sana", default="",
                            help="Sanani qo'lda berish: YYYY-MM-DD.")

    def handle(self, *args, **options):
        sana = self._sana(options["sana"])

        if options["holat"]:
            return self._holat()

        if not sozlamalar.yoqilgan():
            self.stdout.write(self.style.WARNING(
                "SMS moduli O'CHIQ (SMS_ESLATMA_YOQILGAN = False)."
            ))
            if not options["sinov"]:
                self.stdout.write(
                    "  Nima tayyorlanishini ko'rish uchun: manage.py sms_eslatma --sinov"
                )
                return

        if options["sinov"]:
            return self._sinov(sana)

        soni = services.eslatmalarni_navbatga_qoy(sana, majburiy=options["majburiy"])
        if soni:
            self.stdout.write(self.style.SUCCESS(
                f"Tayyor. {soni} ta eslatma navbatga qo'yildi.\n"
                f"Yuborish uchun: saytdagi \"Xabarnoma -> Xabarlar\" bo'limi."
            ))
        else:
            self.stdout.write(
                "Yangi xabar yozilmadi (bugun eslatma kuni emas, qarzdor yo'q yoki "
                "bu oyning xabarlari allaqachon tayyorlangan)."
            )

    # ------------------------------------------------------------------

    def _sana(self, matn):
        if not matn:
            return date.today()
        try:
            return date.fromisoformat(matn)
        except ValueError:
            raise CommandError("Sana YYYY-MM-DD ko'rinishida bo'lishi kerak.")

    def _sinov(self, sana):
        xabarlar = services.sinov_royxati(sana)
        if not xabarlar:
            self.stdout.write("Tayyorlanadigan xabar yo'q.")
            return

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"{sana} holatiga ko'ra {len(xabarlar)} ta xabar (kimga: "
            f"{sozlamalar.kimga()}):"
        ))
        for xabar in xabarlar:
            bolak = services.sms_bolaklari(xabar.matn)
            self.stdout.write(
                f"  {xabar.telefon:<16} {xabar.get_qabul_qiluvchi_display():<4} "
                f"[{len(xabar.matn):>3} belgi / {bolak} SMS]  {xabar.matn}"
            )
        self.stdout.write(self.style.WARNING("\nBu sinov - bazaga hech nima yozilmadi."))

    def _holat(self):
        sanoq = services.navbat_holati()
        self.stdout.write(self.style.MIGRATE_HEADING("Xabarlar:"))
        for kod, nom in (("navbatda", "Navbatda"), ("berildi", "Qurilmada"),
                         ("olindi", "Ilova oldi"), ("jonatildi", "Jo'natildi"),
                         ("xato", "Jo'natilmadi"), ("bekor", "Bekor qilingan")):
            self.stdout.write(f"  {nom:<16} {sanoq.get(kod, 0)}")
        self.stdout.write(f"  {'JAMI':<16} {sanoq.get('jami', 0)}")

        qurilmalar = services.qurilmalar_holati()
        self.stdout.write(self.style.MIGRATE_HEADING("\nQurilmalar:"))
        if not qurilmalar["royxat"]:
            self.stdout.write("  Ulangan qurilma yo'q.")
            return
        for qurilma in qurilmalar["royxat"]:
            self.stdout.write(
                f"  {qurilma.nomi:<24} {qurilma.holat_nomi:<12} {qurilma.aloqa_matni}"
            )
