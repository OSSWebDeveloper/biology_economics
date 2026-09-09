"""Tizimni sinab ko'rish uchun namunaviy ma'lumot qo'shadi.

    python manage.py namuna            # namunaviy ma'lumot qo'shadi
    python manage.py namuna --tozala   # namunaviy ma'lumotlarni o'chiradi

DIQQAT: --tozala barcha o'quvchi, xodim va to'lovlarni o'chiradi.
Haqiqiy ish boshlangandan keyin bu buyruqni ishlatmang.
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Foydalanuvchi
from payments.models import Karta, Tranzaksiya, Usul
from payments.services import barcha_hisoblarni_yangila, oquvchi_balansi, oy_boshi
from staff.models import Xodim, XodimTranzaksiya
from staff.services import maoshlarni_yangila
from students.models import Guruh, Oquvchi

ISMLAR = ["Ali", "Vali", "Zilola", "Madina", "Jasur", "Nodira", "Sardor", "Kamola",
          "Bekzod", "Malika", "Aziz", "Shahnoza", "Doston", "Gulnora", "Temur",
          "Sevara", "Islom", "Dilnoza", "Otabek", "Ziyoda"]
FAMILIYALAR = ["Valiyev", "Karimova", "Rahmonov", "Yusupova", "Tosheva", "Alimov",
               "Nazarova", "Qodirov", "Ergasheva", "Sultonov", "Ismoilova",
               "Xolmatov", "Jo'rayeva", "Sobirov", "Aliyeva"]


class Command(BaseCommand):
    help = "Namunaviy o'quvchi, xodim va to'lovlarni qo'shadi."

    def add_arguments(self, parser):
        parser.add_argument("--tozala", action="store_true",
                            help="Barcha o'quvchi/xodim/to'lovlarni o'chiradi")
        parser.add_argument("--soni", type=int, default=18,
                            help="Nechta o'quvchi qo'shilsin (standart 18)")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["tozala"]:
            # Xodimlarga ochilgan sayt loginlari ham o'chadi, lekin admin va
            # texnik superuser hisoblariga tegilmaydi.
            hisob_idlar = list(
                Xodim.objects.filter(foydalanuvchi__isnull=False)
                .exclude(foydalanuvchi__is_superuser=True)
                .exclude(foydalanuvchi__rol=Foydalanuvchi.Rol.ADMIN)
                .values_list("foydalanuvchi_id", flat=True)
            )
            Tranzaksiya.objects.all().delete()
            XodimTranzaksiya.objects.all().delete()
            Oquvchi.objects.all().delete()
            Xodim.objects.all().delete()
            Guruh.objects.all().delete()
            Karta.objects.all().delete()
            ochirilgan = Foydalanuvchi.objects.filter(pk__in=hisob_idlar).delete()[0]
            self.stdout.write(self.style.WARNING(
                f"Barcha ma'lumot o'chirildi. Xodim loginlari: {ochirilgan} ta."))
            return

        tasodif = random.Random(2026)
        bugun = date.today()

        kartalar = [
            Karta.objects.create(nomi="Humo - asosiy", raqam="9860 1234 5678 1234",
                                 egasi="Biologiya kursi"),
            Karta.objects.create(nomi="Uzcard - zaxira", raqam="8600 8765 4321 8765",
                                 egasi="Biologiya kursi"),
        ]

        guruhlar = [
            Guruh.objects.create(nomi="9-sinf (DTM)", oylik_toluv=Decimal(500000)),
            Guruh.objects.create(nomi="11-sinf (blok)", oylik_toluv=Decimal(700000)),
            Guruh.objects.create(nomi="Abituriyent", oylik_toluv=Decimal(900000)),
        ]

        oquvchilar = []
        for i in range(options["soni"]):
            guruh = tasodif.choice(guruhlar)
            # Ba'zilari bir necha oy oldin, ba'zilari oy o'rtasida kelgan
            kun_oldin = tasodif.choice([120, 95, 70, 62, 45, 30, 22, 14, 7, 3])
            boshlangan = bugun - timedelta(days=kun_oldin)
            oquvchi = Oquvchi.objects.create(
                ism=tasodif.choice(ISMLAR),
                familiya=tasodif.choice(FAMILIYALAR),
                telefon=f"+998 9{tasodif.randint(0, 9)} {tasodif.randint(100, 999)} "
                        f"{tasodif.randint(10, 99)} {tasodif.randint(10, 99)}",
                ota_telefon=f"+998 9{tasodif.randint(0, 9)} {tasodif.randint(100, 999)} "
                            f"{tasodif.randint(10, 99)} {tasodif.randint(10, 99)}",
                ona_telefon="" if i % 3 else
                            f"+998 90 {tasodif.randint(100, 999)} "
                            f"{tasodif.randint(10, 99)} {tasodif.randint(10, 99)}",
                guruh=guruh,
                oylik_toluv=guruh.oylik_toluv,
                boshlangan_sana=boshlangan,
            )
            oquvchilar.append(oquvchi)

        # Ikki o'quvchi kursdan chiqarilgan
        for oquvchi in oquvchilar[:2]:
            oquvchi.faol = False
            oquvchi.chiqarilgan_sana = bugun - timedelta(days=tasodif.randint(5, 25))
            oquvchi.chiqarish_sababi = "boshqa maktabga o'tdi"
            oquvchi.save()

        barcha_hisoblarni_yangila()

        # To'lovlar: kimdir to'liq, kimdir qisman, kimdir oldindan to'lagan
        for oquvchi in oquvchilar:
            qarz = -oquvchi_balansi(oquvchi)
            if qarz <= 0:
                continue
            uslub = tasodif.random()
            if uslub < 0.15:
                continue                                  # umuman to'lamagan
            elif uslub < 0.45:
                summa = (qarz * Decimal("0.5")).quantize(Decimal("1"))
            elif uslub < 0.85:
                summa = qarz
            else:
                summa = qarz + Decimal(tasodif.choice([100000, 200000, 300000]))

            usul = Usul.NAQD if tasodif.random() < 0.45 else Usul.PLASTIK
            karta = tasodif.choice(kartalar) if usul == Usul.PLASTIK else None
            Tranzaksiya.objects.create(
                oquvchi=oquvchi, tur=Tranzaksiya.Tur.TOLOV, summa=summa,
                sana=bugun - timedelta(days=tasodif.randint(0, 20)),
                usul=usul, karta=karta,
                karta_raqami=karta.raqam if karta else "",
                izoh="kurs to'lovi",
            )

        # O'qituvchi bitta o'quvchidan qarz bo'lib qoldi -> oldindan to'lovga o'tadi
        if oquvchilar:
            Tranzaksiya.objects.create(
                oquvchi=oquvchilar[-1], tur=Tranzaksiya.Tur.QARZ,
                summa=Decimal(150000), sana=bugun - timedelta(days=6),
                izoh="3 ta dars o'tkazilmadi",
            )

        xodimlar = [
            Xodim.objects.create(ism="Nilufar", familiya="Ahmedova",
                                 lavozim="administrator", telefon="+998 90 111 22 33",
                                 karta_raqami="9860 0000 1111 2222",
                                 oylik_maosh=Decimal(4000000),
                                 ishga_kirgan_sana=bugun - timedelta(days=200)),
            Xodim.objects.create(ism="Sanjar", familiya="Rustamov",
                                 lavozim="yordamchi o'qituvchi", telefon="+998 91 222 33 44",
                                 karta_raqami="8600 0000 3333 4444",
                                 oylik_maosh=Decimal(3000000),
                                 ishga_kirgan_sana=bugun - timedelta(days=75)),
            Xodim.objects.create(ism="Zuhra", familiya="Normatova",
                                 lavozim="farrosh", telefon="+998 93 333 44 55",
                                 oylik_maosh=Decimal(1500000),
                                 ishga_kirgan_sana=bugun - timedelta(days=40)),
        ]
        maoshlarni_yangila()

        joriy_oy = oy_boshi(bugun)
        for xodim in xodimlar:
            # o'tgan oylar to'liq yopilgan, joriy oyga avans berilgan
            for tranzaksiya in xodim.tranzaksiyalar.filter(
                tur=XodimTranzaksiya.Tur.HISOB, davr__lt=joriy_oy
            ):
                XodimTranzaksiya.objects.create(
                    xodim=xodim, tur=XodimTranzaksiya.Tur.OYLIK,
                    summa=tranzaksiya.summa,
                    sana=tranzaksiya.davr + timedelta(days=32),
                    usul=Usul.PLASTIK if xodim.karta_raqami else Usul.NAQD,
                    karta_raqami=xodim.karta_raqami,
                    izoh="oylik to'liq berildi",
                )
            avans = (xodim.oylik_maosh * Decimal("0.4")).quantize(Decimal("1"))
            XodimTranzaksiya.objects.create(
                xodim=xodim, tur=XodimTranzaksiya.Tur.AVANS, summa=avans,
                sana=min(joriy_oy + timedelta(days=9), bugun),
                usul=Usul.NAQD, izoh="avans",
            )

        self.stdout.write(self.style.SUCCESS(
            f"Namuna tayyor: {len(oquvchilar)} o'quvchi, {len(guruhlar)} guruh, "
            f"{len(xodimlar)} xodim, {Tranzaksiya.objects.count()} tranzaksiya."
        ))
