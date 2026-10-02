from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, ProtectedError, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .decorators import admin_required
from .forms import AppointmentForm, CategoryForm, ServiceForm, SignupForm
from .models import Appointment, Category, Service, User


# ----- Dashboard -----

@login_required
def index(request):
    today = timezone.localdate()
    appointments = Appointment.objects.visible_to(request.user)
    active_appointments = appointments.exclude(status=Appointment.Status.CANCELLED)
    upcoming_appointments = active_appointments.filter(date__gte=today)
    top_services = []

    if request.user.is_admin:
        revenue = active_appointments.filter(status=Appointment.Status.CONFIRMED).aggregate(
            total=Sum("service__price")
        )["total"] or 0
        stats = [
            {"label": "Citas hoy", "value": active_appointments.filter(date=today).count(), "icon": "bi-calendar-day"},
            {"label": "Por confirmar", "value": appointments.filter(status=Appointment.Status.PENDING).count(), "icon": "bi-hourglass-split"},
            {"label": "Clientes", "value": User.objects.filter(role=User.Role.CLIENT).count(), "icon": "bi-people"},
            {"label": "Ingresos confirmados", "value": f"${revenue}", "icon": "bi-cash-coin"},
        ]
        top_services = list(
            Service.objects.annotate(
                appointment_count=Count(
                    "appointments",
                    filter=Q(appointments__status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED]),
                )
            )
            .filter(appointment_count__gt=0)
            .order_by("-appointment_count")[:5]
        )
    else:
        stats = [
            {"label": "Próximas citas", "value": upcoming_appointments.count(), "icon": "bi-calendar-event"},
            {"label": "Confirmadas", "value": appointments.filter(status=Appointment.Status.CONFIRMED).count(), "icon": "bi-check-circle"},
            {"label": "Total de citas", "value": appointments.count(), "icon": "bi-journal-text"},
        ]

    return render(request, "core/index.html", {
        "stats": stats,
        "upcoming_appointments": upcoming_appointments[:5],
        "top_services": top_services,
        "max_appointment_count": top_services[0].appointment_count if top_services else 0,
    })


# ----- Registro -----

def signup(request):
    if request.user.is_authenticated:
        return redirect("core:index")
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Cuenta creada. ¡Bienvenido!")
            return redirect("core:index")
    else:
        form = SignupForm()
    return render(request, "core/form.html", {
        "form": form,
        "title": "Crear cuenta",
        "submit_label": "Registrarme",
        "cancel_url": reverse("login"),
    })


# ----- Servicios -----

@login_required
def service_list(request):
    # prefetch_related trae todas las categorías en 1 consulta extra, en vez de 1 por servicio (N+1).
    services = Service.objects.prefetch_related("categories")
    return render(request, "core/service_list.html", {"services": services})


@admin_required
def service_create(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Servicio creado.")
            return redirect("core:service_list")
    else:
        form = ServiceForm()
    return render(request, "core/form.html", {
        "form": form,
        "title": "Nuevo servicio",
        "cancel_url": reverse("core:service_list"),
    })


@login_required
def service_detail(request, pk):
    service = get_object_or_404(Service.objects.prefetch_related("categories"), pk=pk)
    return render(request, "core/service_detail.html", {"service": service})


@admin_required
@require_POST
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    try:
        service.delete()
    except ProtectedError:
        messages.error(request, "No se puede eliminar: el servicio tiene citas asociadas.")
        return redirect("core:service_detail", pk=pk)
    messages.success(request, "Servicio eliminado.")
    return redirect("core:service_list")


# ----- Categorías -----

@admin_required
def category_list(request):
    categories = Category.objects.annotate(service_count=Count("services"))
    return render(request, "core/category_list.html", {"categories": categories})


@admin_required
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría creada.")
            return redirect("core:category_list")
    else:
        form = CategoryForm()
    return render(request, "core/form.html", {
        "form": form,
        "title": "Nueva categoría",
        "cancel_url": reverse("core:category_list"),
    })


@admin_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        # instance=category: el form actualiza ese registro en vez de crear uno nuevo.
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría actualizada.")
            return redirect("core:category_list")
    else:
        form = CategoryForm(instance=category)
    return render(request, "core/form.html", {
        "form": form,
        "title": "Editar categoría",
        "cancel_url": reverse("core:category_list"),
    })


@admin_required
@require_POST
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.success(request, "Categoría eliminada.")
    return redirect("core:category_list")


# ----- Citas -----

@login_required
def appointment_list(request):
    appointments = Appointment.objects.visible_to(request.user)
    current_status = request.GET.get("status", "")
    if current_status in Appointment.Status.values:
        appointments = appointments.filter(status=current_status)
    return render(request, "core/appointment_list.html", {
        "appointments": appointments,
        "statuses": Appointment.Status.choices,
        "current_status": current_status,
    })


@login_required
def appointment_create(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            # commit=False: crea el objeto sin guardarlo para completar los campos que no vienen del form.
            appointment = form.save(commit=False)
            appointment.client = request.user
            appointment.save()
            messages.success(request, "Cita agendada. Queda pendiente de confirmación.")
            return redirect("core:appointment_list")
    else:
        # ?service=3 en la URL preselecciona el servicio (botón "Agendar" de la lista de servicios).
        form = AppointmentForm(initial={"service": request.GET.get("service")})
    return render(request, "core/form.html", {
        "form": form,
        "title": "Agendar cita",
        "submit_label": "Agendar",
        "cancel_url": reverse("core:appointment_list"),
    })


@login_required
@require_POST
def appointment_change_status(request, pk):
    # visible_to: un cliente no puede tocar citas ajenas aunque cambie el id en la URL (da 404).
    appointment = get_object_or_404(Appointment.objects.visible_to(request.user), pk=pk)
    new_status = request.POST.get("status")
    if appointment.can_change_to(new_status, request.user):
        appointment.status = new_status
        appointment.save(update_fields=["status"])
        messages.success(request, f"Cita {appointment.get_status_display().lower()}.")
    else:
        messages.error(request, "No se puede hacer ese cambio de estado.")
    return redirect("core:appointment_list")
