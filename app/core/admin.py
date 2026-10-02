from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Appointment, Category, Service, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Rol en la app", {"fields": ("role",)}),)
    list_display = ("username", "email", "role", "is_superuser")
    list_filter = ("role", "is_superuser")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "duration_minutes")
    filter_horizontal = ("categories",)
    search_fields = ("name",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("date", "time", "service", "client", "status")
    list_filter = ("status", "service")
    list_select_related = ("service", "client")
