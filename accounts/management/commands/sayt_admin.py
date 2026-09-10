"""Sayt panelining admin hisobini yaratadi yoki parolini yangilaydi.

Bu hisob Django admin (superuser) hisobidan BUTUNLAY ALOHIDA:
    python manage.py sayt_admin --login admin --parol 12345 --ism "Odil" --familiya "Kenjayev"
"""
from django.core.management.base import BaseCommand

from accounts.models import Foydalanuvchi


class Command(BaseCommand):
    help = "Sayt paneliga kiradigan admin hisobini yaratadi/yangilaydi."

    def add_arguments(self, parser):
        parser.add_argument("--login", required=True, help="Sayt paneli logini")
        parser.add_argument("--parol", required=True, help="Sayt paneli paroli")
        parser.add_argument("--ism", default="", help="Ism")
        parser.add_argument("--familiya", default="", help="Familiya")
        parser.add_argument("--oqituvchi", action="store_true",
                            help="Admin emas, o'qituvchi sifatida yaratish")

    def handle(self, *args, **options):
        rol = (Foydalanuvchi.Rol.OQITUVCHI if options["oqituvchi"]
               else Foydalanuvchi.Rol.ADMIN)
        obyekt, yangi = Foydalanuvchi.objects.get_or_create(
            username=options["login"],
            defaults={"rol": rol},
        )
        obyekt.rol = rol
        obyekt.first_name = options["ism"] or obyekt.first_name
        obyekt.last_name = options["familiya"] or obyekt.last_name
        obyekt.saytga_kira_oladi = True
        obyekt.is_active = True
        obyekt.set_password(options["parol"])
        obyekt.save()

        holat = "yaratildi" if yangi else "paroli yangilandi"
        self.stdout.write(self.style.SUCCESS(
            f"Sayt hisobi '{obyekt.username}' ({obyekt.get_rol_display()}) {holat}."
        ))
