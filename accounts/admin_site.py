from django.contrib.admin import AdminSite


class BoshqaruvAdminSite(AdminSite):
    """Texnik Django admin paneli.

    Sayt panelidan butunlay alohida: bu yerga FAQAT superuser (`createsuperuser`
    orqali yaratilgan texnik hisob) kira oladi. Sayt admini (rol="admin") bu
    panelga kira olmaydi va aksincha - ikkalasining login/paroli boshqa-boshqa.
    """

    site_title = "Texnik boshqaruv"
    site_header = "Biologiya kursi - texnik boshqaruv (Django admin)"
    index_title = "Ma'lumotlar bazasi"

    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser
