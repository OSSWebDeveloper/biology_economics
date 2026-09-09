"""Asosiy manzillar.

  /boshqaruv/  -> Django admin (texnik panel, faqat superuser)
  qolgani      -> sayt paneli (o'z login/paroli bilan)
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("boshqaruv/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("", include("accounts.urls")),
    path("oquvchilar/", include("students.urls")),
    path("tolovlar/", include("payments.urls")),
    path("xodimlar/", include("staff.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
