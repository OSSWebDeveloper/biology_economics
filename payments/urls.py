from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("", views.tolovlar, name="tolovlar"),
    path("qoshish/<int:oquvchi_id>/", views.tolov_qoshish, name="tolov_qoshish"),
    path("tez/<int:oquvchi_id>/oyna/", views.tez_tolov_oyna, name="tez_tolov_oyna"),
    path("tez/<int:oquvchi_id>/", views.tez_tolov, name="tez_tolov"),
    path("<int:pk>/ochirish/", views.tolov_ochirish, name="tolov_ochirish"),
    path("kartalar/", views.kartalar, name="kartalar"),
    path("kartalar/yangi/", views.karta_saqlash, name="karta_yangi"),
    path("kartalar/<int:pk>/", views.karta_saqlash, name="karta_tahrir"),
    path("kartalar/<int:pk>/ochirish/", views.karta_ochirish, name="karta_ochirish"),
]
