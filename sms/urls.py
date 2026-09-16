"""Admin uchun "Xabarnoma" bo'limining manzillari (/xabarnoma/...)."""
from django.urls import path

from . import views

app_name = "sms"

urlpatterns = [
    path("", views.bosh, name="bosh"),
    path("kod/", views.kod_yarat, name="kod_yarat"),
    path("qurilma/<int:pk>/ochir/", views.qurilma_ochir, name="qurilma_ochir"),
    path("qurilma/<int:pk>/uzish/", views.qurilma_uzish, name="qurilma_uzish"),
    path("sim/<int:pk>/ochir/", views.sim_ochir, name="sim_ochir"),

    path("xabarlar/", views.xabarlar, name="xabarlar"),
    path("xabarlar/yuborish/", views.yuborish, name="yuborish"),
    path("xabarlar/tayyorla/", views.navbatni_tayyorla, name="navbatni_tayyorla"),

    path("xatolar/", views.xatolar, name="xatolar"),
    path("xatolar/<int:pk>/qayta/", views.qayta_urin, name="qayta_urin"),
    path("xatolar/qayta/", views.hammasini_qayta_urin, name="hammasini_qayta_urin"),

    path("holat.json", views.holat_json, name="holat_json"),
]
