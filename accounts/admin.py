from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Foydalanuvchi


@admin.register(Foydalanuvchi)
class FoydalanuvchiAdmin(UserAdmin):
    list_display = ("username", "first_name", "last_name", "rol", "saytga_kira_oladi",
                    "is_superuser", "is_active")
    list_filter = ("rol", "saytga_kira_oladi", "is_superuser", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Sayt paneli", {"fields": ("rol", "telefon", "saytga_kira_oladi")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Sayt paneli", {"fields": ("rol", "telefon", "saytga_kira_oladi")}),
    )
