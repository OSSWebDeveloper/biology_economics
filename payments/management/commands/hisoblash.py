"""Oylik hisoblarni ochish.

Har oyning 1-sanasida ishga tushirilsa yaxshi (Windows Task Scheduler):
    python manage.py hisoblash

Amalda sayt sahifalari ochilganda ham avtomatik ishlaydi, bu buyruq
zaxira sifatida va sayt uzoq ochilmagan holatlar uchun.
"""
from django.core.management.base import BaseCommand

from payments.services import barcha_hisoblarni_yangila
from staff.services import maoshlarni_yangila


class Command(BaseCommand):
    help = "O'quvchilarning kurs to'lovlari va xodimlar oyligini hisoblab qo'yadi."

    def handle(self, *args, **options):
        oquvchi_soni = barcha_hisoblarni_yangila()
        xodim_soni = maoshlarni_yangila()
        self.stdout.write(self.style.SUCCESS(
            f"Tayyor. O'quvchilarga {oquvchi_soni} ta, xodimlarga {xodim_soni} ta "
            f"yangi hisob ochildi."
        ))
