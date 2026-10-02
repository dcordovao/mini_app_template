from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import SignupForm, ServiceForm
from .models import Service
from django.contrib import messages
from django.views.decorators.http import require_POST


@login_required
def index(request):
    return render(request, "core/index.html")


@login_required
def services(request):
    return render(request, "services.html", {"services_list": Service.objects.all()})


@login_required
def service_create(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Servicio creado.")
            return redirect("core:services")
    else:
        form = ServiceForm()
    return render(request, "core/service_form.html", {"form": form, "title": "Nuevo servicio"})


@login_required
def service_detail(request, pk):
    service = get_object_or_404(Service, pk=pk)
    return render(request, "core/service_detail.html", {"service": service})


@login_required
@require_POST
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    service.delete()
    messages.success(request, "Servicio eliminado.")
    return redirect("core:services")