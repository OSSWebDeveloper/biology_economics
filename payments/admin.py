from django.contrib import admin

from .models import Karta, Tranzaksiya


@admin.register(Karta)
class KartaAdmin(admin.ModelAdmin):
    list_display = ("nomi", "raqam", "egasi", "faol")
    list_filter = ("faol",)


@admin.register(Tranzaksiya)
class TranzaksiyaAdmin(admin.ModelAdmin):
    list_display = ("sana", "oquvchi", "tur", "summa", "usul", "karta_raqami", "davr")
    list_filter = ("tur", "usul", "sana")
    search_fields = ("oquvchi__ism", "oquvchi__familiya", "izoh")
    date_hierarchy = "sana"
    autocomplete_fields = ("oquvchi",)
