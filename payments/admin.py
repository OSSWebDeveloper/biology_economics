from django.contrib import admin

from .models import Tranzaksiya


@admin.register(Tranzaksiya)
class TranzaksiyaAdmin(admin.ModelAdmin):
    list_display = ("sana", "oquvchi", "tur", "summa", "usul", "davr")
    list_filter = ("tur", "usul", "sana")
    search_fields = ("oquvchi__ism", "oquvchi__familiya", "izoh")
    date_hierarchy = "sana"
    autocomplete_fields = ("oquvchi",)
