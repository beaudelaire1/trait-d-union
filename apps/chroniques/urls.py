from django.urls import path
from . import views

app_name = "chroniques"

urlpatterns = [
    path("", views.article_list, name="list"),
    path("<slug:slug>/", views.article_detail, name="detail"),
]
