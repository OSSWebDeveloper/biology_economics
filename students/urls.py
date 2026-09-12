from django.urls import path

from . import views

app_name = "students"

urlpatterns = [
    path("", views.oquvchilar, name="oquvchilar"),
    path("yangi/", views.oquvchi_saqlash, name="oquvchi_yangi"),
    path("arxiv/", views.arxiv, name="arxiv"),
    path("arxiv/<int:pk>/chiqarish/", views.arxivdan_chiqarish, name="arxivdan_chiqarish"),
    path("guruhlar/", views.guruhlar, name="guruhlar"),
    path("guruhlar/yangi/", views.guruh_saqlash, name="guruh_yangi"),
    path("guruhlar/<int:pk>/oyna/", views.guruh_oyna, name="guruh_oyna"),
    path("guruhlar/<int:pk>/", views.guruh_saqlash, name="guruh_tahrir"),
    path("guruhlar/<int:pk>/ochirish/", views.guruh_ochirish, name="guruh_ochirish"),
    path("<int:pk>/", views.oquvchi, name="oquvchi"),
    path("<int:pk>/tahrirlash/", views.oquvchi_saqlash, name="oquvchi_tahrir"),
    path("<int:pk>/chiqarish/", views.oquvchi_chiqarish, name="oquvchi_chiqarish"),
    path("<int:pk>/guruh-oyna/", views.oquvchi_guruh_oyna, name="oquvchi_guruh_oyna"),
    path("<int:pk>/guruhni-ozgartirish/", views.oquvchi_guruh_kochirish,
         name="oquvchi_guruh_kochirish"),
    path("<int:pk>/arxiv-oyna/", views.oquvchi_arxiv_oyna, name="oquvchi_arxiv_oyna"),
    path("<int:pk>/arxivlash/", views.oquvchi_arxivlash, name="oquvchi_arxivlash"),
    path("<int:pk>/qaytarish/", views.oquvchi_qaytarish, name="oquvchi_qaytarish"),
    path("<int:pk>/ochirish/", views.oquvchi_ochirish, name="oquvchi_ochirish"),
]
