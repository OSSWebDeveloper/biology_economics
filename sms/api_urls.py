"""Telefondagi ilova uchun manzillar (/sms/...).

Odam uchun emas - faqat ilova ishlatadi. Modul o'chiq bo'lsa 404 qaytaradi.
"""
from django.urls import path

from . import api

app_name = "sms_api"

urlpatterns = [
    path("ulan/", api.ulan, name="ulan"),
    path("tekshir/", api.tekshir, name="tekshir"),
    path("simlar/", api.simlar, name="simlar"),
    path("navbat/", api.navbat, name="navbat"),
    path("holat/", api.holat, name="holat"),
]
