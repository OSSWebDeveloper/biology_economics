"""Guruh o'qituvchisi endi xodim emas, sayt hisobiga bog'lanadi.

Sabab: kursxona boshlig'i xodimlar ro'yxatida yo'q, lekin u ham guruhga
o'qituvchi bo'lib qayd etilishi kerak.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def hisobga_kochir(apps, schema_editor):
    """Eski xodim bog'lanishini uning sayt hisobiga o'tkazadi."""
    Guruh = apps.get_model("students", "Guruh")
    Foydalanuvchi = apps.get_model("accounts", "Foydalanuvchi")

    admin = (Foydalanuvchi.objects.filter(rol="admin", is_superuser=False)
             .order_by("id").first())

    for guruh in Guruh.objects.all():
        hisob = None
        if guruh.oqituvchi_id:
            xodim = apps.get_model("staff", "Xodim").objects.filter(
                pk=guruh.oqituvchi_id).first()
            if xodim:
                hisob = xodim.foydalanuvchi
        # O'qituvchisi yo'q guruhlar adminning zimmasida qoladi
        guruh.oqituvchi_hisob = hisob or admin
        guruh.save(update_fields=["oqituvchi_hisob"])


def orqaga(apps, schema_editor):
    Guruh = apps.get_model("students", "Guruh")
    Xodim = apps.get_model("staff", "Xodim")
    for guruh in Guruh.objects.all():
        xodim = None
        if guruh.oqituvchi_hisob_id:
            xodim = Xodim.objects.filter(
                foydalanuvchi_id=guruh.oqituvchi_hisob_id).first()
        guruh.oqituvchi_id = xodim.pk if xodim else None
        guruh.save(update_fields=["oqituvchi"])


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0006_guruh_oqituvchi"),
        ("staff", "0004_remove_xodim_karta_raqami_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="guruh",
            name="oqituvchi_hisob",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="guruhlar_vaqtincha",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(hisobga_kochir, orqaga),
        migrations.RemoveField(model_name="guruh", name="oqituvchi"),
        migrations.RenameField(
            model_name="guruh", old_name="oqituvchi_hisob", new_name="oqituvchi",
        ),
        migrations.AlterField(
            model_name="guruh",
            name="oqituvchi",
            field=models.ForeignKey(
                blank=True,
                help_text="Bo'sh qoldirilsa, guruhni yaratgan admin o'qituvchi sifatida qayd etiladi.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="guruhlar",
                to=settings.AUTH_USER_MODEL,
                verbose_name="O'qituvchi",
            ),
        ),
    ]
