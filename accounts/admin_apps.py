from django.contrib.admin.apps import AdminConfig


class BoshqaruvAdminConfig(AdminConfig):
    """Django admin panelini o'z AdminSite'imiz bilan almashtiradi.

    settings.INSTALLED_APPS ichida "django.contrib.admin" o'rniga shu ishlatiladi.
    """

    default_site = "accounts.admin_site.BoshqaruvAdminSite"
