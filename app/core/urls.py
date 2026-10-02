from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path("signup/", views.signup, name="signup"),

    path("services/", views.service_list, name="service_list"),
    path("services/new/", views.service_create, name="service_create"),
    path("services/<int:pk>/", views.service_detail, name="service_detail"),
    path("services/<int:pk>/delete/", views.service_delete, name="service_delete"),

    path("categories/", views.category_list, name="category_list"),
    path("categories/new/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_update, name="category_update"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),

    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointments/new/", views.appointment_create, name="appointment_create"),
    path("appointments/<int:pk>/status/", views.appointment_change_status, name="appointment_change_status"),
]
