from django.urls import path

from . import views

app_name = "staff"

urlpatterns = [
    path("", views.xodimlar, name="xodimlar"),
    path("yangi/", views.xodim_saqlash, name="xodim_yangi"),
    path("tolovlar/", views.oylik_tolovlari, name="tolovlar"),
    path("<int:pk>/tez/oyna/", views.tez_oylik_oyna, name="tez_oylik_oyna"),
    path("<int:pk>/tez/", views.tez_oylik, name="tez_oylik"),
    path("tolov/<int:pk>/ochirish/", views.tolov_ochirish, name="tolov_ochirish"),
    path("<int:pk>/", views.xodim, name="xodim"),
    path("<int:pk>/tahrirlash/", views.xodim_saqlash, name="xodim_tahrir"),
    path("<int:pk>/maosh/", views.maosh_tayinlash, name="maosh_tayinlash"),
    path("<int:pk>/holat/", views.xodim_ishdan_boshatish, name="xodim_holat"),
    path("<int:pk>/hisob/", views.xodim_hisob, name="xodim_hisob"),
    path("<int:pk>/hisob/boglash/", views.xodim_hisob_boglash, name="xodim_hisob_boglash"),
    path("<int:pk>/hisob/uzish/", views.xodim_hisob_uzish, name="xodim_hisob_uzish"),
    path("<int:pk>/ochirish/", views.xodim_ochirish, name="xodim_ochirish"),
]
