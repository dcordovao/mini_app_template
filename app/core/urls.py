from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path("services/", views.services, name="services"),
    path("services/new/", views.service_create, name="service_create"),
    path("services/<int:pk>/", views.service_detail, name="service_detail"),
    path("services/<int:pk>/delete/", views.service_delete, name="service_delete"),
]
