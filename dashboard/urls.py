from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.bosh, name="bosh"),
    path("moliya/", views.moliya, name="moliya"),
]
