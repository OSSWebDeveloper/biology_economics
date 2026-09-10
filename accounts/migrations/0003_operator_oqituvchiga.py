"""Eski 'operator' roli 'oqituvchi' ga o'tkaziladi."""
from django.db import migrations


def oldinga(apps, schema_editor):
    Foydalanuvchi = apps.get_model("accounts", "Foydalanuvchi")
    Foydalanuvchi.objects.filter(rol="operator").update(rol="oqituvchi")


def orqaga(apps, schema_editor):
    Foydalanuvchi = apps.get_model("accounts", "Foydalanuvchi")
    Foydalanuvchi.objects.filter(rol="oqituvchi").update(rol="operator")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_alter_foydalanuvchi_rol"),
    ]

    operations = [
        migrations.RunPython(oldinga, orqaga),
    ]
