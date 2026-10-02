from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import User, Service

class SignupForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", )

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ("name", "price", "description",)