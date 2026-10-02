from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import Appointment, Category, Service, User


class SignupForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name",)


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ("name", "price", "duration_minutes", "description", "categories")
        widgets = {"categories": forms.CheckboxSelectMultiple}


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ("service", "date", "time", "notes")
        widgets = {
            # type="date"/"time" hace que el navegador muestre su selector nativo.
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_date(self):
        date = self.cleaned_data["date"]
        if date < timezone.localdate():
            raise forms.ValidationError("No se puede agendar en una fecha pasada.")
        return date

    def clean(self):
        cleaned_data = super().clean()
        service = cleaned_data.get("service")
        date = cleaned_data.get("date")
        time = cleaned_data.get("time")
        if service and date and time:
            slot_taken = (
                Appointment.objects.filter(service=service, date=date, time=time)
                .exclude(status=Appointment.Status.CANCELLED)
                .exclude(pk=self.instance.pk)
                .exists()
            )
            if slot_taken:
                raise forms.ValidationError("Ese horario ya está reservado para este servicio.")
        return cleaned_data
