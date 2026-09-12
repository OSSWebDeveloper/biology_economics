from django.contrib import admin

from .models import Arxiv, Guruh, Oquvchi


@admin.register(Guruh)
class GuruhAdmin(admin.ModelAdmin):
    list_display = ("nomi", "oylik_toluv", "faol")
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


@admin.register(Arxiv)
class ArxivAdmin(admin.ModelAdmin):
    list_display = ("oquvchi", "sabab", "guruh_nomi", "biologiya_bali", "jami_ball",
                    "sertifikat", "sana")
    list_filter = ("sabab", "sana")
    search_fields = ("oquvchi__ism", "oquvchi__familiya", "guruh_nomi", "sertifikat")
    date_hierarchy = "sana"
