from django.contrib import admin

from .models import Xodim, XodimTranzaksiya


@admin.register(Xodim)
class XodimAdmin(admin.ModelAdmin):
    list_display = ("familiya", "ism", "oylik_maosh", "telefon", "faol")
    list_filter = ("faol",)
    search_fields = ("ism", "familiya", "telefon")


@admin.register(XodimTranzaksiya)
class XodimTranzaksiyaAdmin(admin.ModelAdmin):
    list_display = ("sana", "xodim", "tur", "summa", "usul", "davr")
    list_filter = ("tur", "usul", "sana")
    search_fields = ("xodim__ism", "xodim__familiya", "izoh")
    date_hierarchy = "sana"
    autocomplete_fields = ("xodim",)
