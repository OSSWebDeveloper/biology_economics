from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("kirish/", views.SaytKirish.as_view(), name="kirish"),
    path("chiqish/", views.SaytChiqish.as_view(), name="chiqish"),
]
