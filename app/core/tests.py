from datetime import time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import AppointmentForm
from .models import Appointment, Service, User


class AppTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user("admin_test", password="pass12345", role=User.Role.ADMIN)
        cls.client_user = User.objects.create_user("client_test", password="pass12345")
        cls.other_client = User.objects.create_user("other_test", password="pass12345")
        cls.service = Service.objects.create(name="Corte", price=5000)
        cls.tomorrow = timezone.localdate() + timedelta(days=1)

    def book(self, client, status=Appointment.Status.PENDING):
        return Appointment.objects.create(
            client=client, service=self.service, date=self.tomorrow, time=time(10, 0), status=status
        )


class SignupTests(AppTestCase):
    def test_signup_creates_client_and_logs_in(self):
        response = self.client.post(reverse("core:signup"), {
            "username": "nuevo",
            "password1": "Clave-segura-123",
            "password2": "Clave-segura-123",
        })
        self.assertRedirects(response, reverse("core:index"))
        user = User.objects.get(username="nuevo")
        self.assertEqual(user.role, User.Role.CLIENT)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)


class PermissionTests(AppTestCase):
    def test_client_cannot_create_service(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("core:service_create"))
        self.assertEqual(response.status_code, 403)

    def test_client_sees_only_own_appointments(self):
        own = self.book(self.client_user)
        Appointment.objects.create(
            client=self.other_client, service=self.service, date=self.tomorrow, time=time(11, 0)
        )
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("core:appointment_list"))
        self.assertEqual(list(response.context["appointments"]), [own])

    def test_client_cannot_confirm_appointment(self):
        appointment = self.book(self.client_user)
        self.client.force_login(self.client_user)
        self.client.post(
            reverse("core:appointment_change_status", args=[appointment.pk]), {"status": "confirmed"}
        )
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.PENDING)


class AppointmentRulesTests(AppTestCase):
    def form_for_booked_slot(self):
        return AppointmentForm(data={"service": self.service.pk, "date": self.tomorrow, "time": "10:00"})

    def test_double_booking_is_rejected(self):
        self.book(self.client_user)
        self.assertFalse(self.form_for_booked_slot().is_valid())

    def test_cancelled_slot_can_be_booked_again(self):
        self.book(self.client_user, status=Appointment.Status.CANCELLED)
        self.assertTrue(self.form_for_booked_slot().is_valid())

    def test_service_with_appointments_cannot_be_deleted(self):
        self.book(self.client_user)
        self.client.force_login(self.admin)
        self.client.post(reverse("core:service_delete", args=[self.service.pk]))
        self.assertTrue(Service.objects.filter(pk=self.service.pk).exists())


class DashboardTests(AppTestCase):
    def test_dashboard_renders_for_each_role(self):
        self.book(self.client_user)
        for user in (self.admin, self.client_user):
            self.client.force_login(user)
            response = self.client.get(reverse("core:index"))
            self.assertEqual(response.status_code, 200)
