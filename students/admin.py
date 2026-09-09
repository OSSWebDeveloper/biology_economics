from django.contrib import admin

from .models import Guruh, Oquvchi


@admin.register(Guruh)
class GuruhAdmin(admin.ModelAdmin):
    list_display = ("nomi", "oylik_toluv", "jadval", "faol")
    list_filter = ("faol",)
    search_fields = ("nomi",)


@admin.register(Oquvchi)
class OquvchiAdmin(admin.ModelAdmin):
    list_display = ("familiya", "ism", "guruh", "telefon", "oylik_toluv",
                    "boshlangan_sana", "faol")
    list_filter = ("faol", "guruh")
    search_fields = ("ism", "familiya", "telefon", "ota_telefon", "ona_telefon")
    date_hierarchy = "boshlangan_sana"
    autocomplete_fields = ("guruh",)
