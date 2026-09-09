from django.urls import path

from . import views

app_name = "staff"

urlpatterns = [
    path("", views.xodimlar, name="xodimlar"),
    path("yangi/", views.xodim_saqlash, name="xodim_yangi"),
    path("tolovlar/", views.oylik_tolovlari, name="tolovlar"),
    path("tolov/qoshish/<int:xodim_id>/", views.tolov_qoshish, name="tolov_qoshish"),
    path("tolov/<int:pk>/ochirish/", views.tolov_ochirish, name="tolov_ochirish"),
    path("<int:pk>/", views.xodim, name="xodim"),
    path("<int:pk>/oyna/", views.xodim_oyna, name="xodim_oyna"),
    path("<int:pk>/tahrirlash/", views.xodim_saqlash, name="xodim_tahrir"),
    path("<int:pk>/maosh/", views.maosh_tayinlash, name="maosh_tayinlash"),
    path("<int:pk>/holat/", views.xodim_ishdan_boshatish, name="xodim_holat"),
    path("<int:pk>/ochirish/", views.xodim_ochirish, name="xodim_ochirish"),
]
