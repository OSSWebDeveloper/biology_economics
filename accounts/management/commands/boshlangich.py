"""Birinchi o'rnatishdan keyingi tayyorgarlik (ORNATISH.bat shuni chaqiradi).

Bir necha marta ishga tushirilsa ham xavfsiz:
  * maxfiy kalit fayli bo'lmasa - yaratadi;
  * birorta ham foydalanuvchi bo'lmasa - sayt admin hisobini ochadi;
  * hisob allaqachon bor bo'lsa - hech nimaga tegmaydi.
"""
import secrets
import string

from django.conf import settings
from django.core.management.base import BaseCommand

from accounts.models import Foydalanuvchi

BELGILAR = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"


class Command(BaseCommand):
    help = "Birinchi ishga tushirish uchun kalit va admin hisobini tayyorlaydi."

    def add_arguments(self, parser):
        parser.add_argument("--login", default="admin", help="Sayt admini logini")
        parser.add_argument("--parol", default="", help="Parol (bo'sh bo'lsa tasodifiy)")

    def handle(self, *args, **options):
        self._kalit()
        self._admin(options["login"], options["parol"])

    def _kalit(self):
        fayl = settings.BASE_DIR / "maxfiy_kalit.txt"
        if fayl.exists() and fayl.read_text(encoding="utf-8").strip():
            self.stdout.write("Maxfiy kalit joyida.")
            return
        fayl.write_text("".join(secrets.choice(BELGILAR) for _ in range(64)),
                        encoding="utf-8")
        self.stdout.write(self.style.SUCCESS("Yangi maxfiy kalit yaratildi."))

    def _admin(self, login, parol):
        if Foydalanuvchi.objects.exists():
            nomlar = ", ".join(
                Foydalanuvchi.objects.filter(saytga_kira_oladi=True)
                .values_list("username", flat=True)
            )
            self.stdout.write(f"Hisoblar mavjud, o'zgartirilmadi. Sayt logini: {nomlar or 'yoq'}")
            return

        parol = parol or "".join(secrets.choice(string.ascii_lowercase + string.digits)
                                 for _ in range(10))
        Foydalanuvchi.objects.create_user(
            username=login, password=parol,
            rol=Foydalanuvchi.Rol.ADMIN,
            first_name="Odil", last_name="Kenjayev",
            saytga_kira_oladi=True,
        )
        self.stdout.write(self.style.SUCCESS("Sayt admin hisobi yaratildi."))
        self.stdout.write(self.style.WARNING(f"    login: {login}"))
        self.stdout.write(self.style.WARNING(f"    parol: {parol}"))
        self.stdout.write("Parolni almashtirish: manage.py sayt_admin --login "
                          f"{login} --parol YANGI_PAROL")
