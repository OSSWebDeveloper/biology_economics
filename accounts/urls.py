from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("kirish/", views.SaytKirish.as_view(), name="kirish"),
    path("chiqish/", views.SaytChiqish.as_view(), name="chiqish"),
    path("shaxsiy/", views.shaxsiy, name="shaxsiy"),
    path("shaxsiy/yangi-foydalanuvchi/", views.foydalanuvchi_saqlash,
         name="foydalanuvchi_yangi"),
    path("shaxsiy/foydalanuvchi/<int:pk>/", views.foydalanuvchi_saqlash,
         name="foydalanuvchi_tahrir"),
    path("shaxsiy/foydalanuvchi/<int:pk>/ochirish/", views.foydalanuvchi_ochirish,
         name="foydalanuvchi_ochirish"),
]
