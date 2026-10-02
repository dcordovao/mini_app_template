from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrador"
        CLIENT = "client", "Cliente"

    # Quien se registra desde /signup/ queda como cliente; los admin se asignan desde /admin/.
    role = models.CharField("Rol", max_length=10, choices=Role.choices, default=Role.CLIENT)

    @property
    def is_admin(self):
        return self.is_superuser or self.role == self.Role.ADMIN


class Category(models.Model):
    name = models.CharField("Nombre", max_length=50, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "categoría"
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.name


class Service(models.Model):
    name = models.CharField("Nombre", max_length=50)
    price = models.IntegerField("Precio")
    duration_minutes = models.PositiveIntegerField("Duración (minutos)", default=30)
    description = models.CharField("Descripción", max_length=100, default="Soy un servicio")
    # N-N simple: un servicio tiene varias categorías y una categoría agrupa varios servicios.
    categories = models.ManyToManyField(
        Category, related_name="services", blank=True, verbose_name="Categorías"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "servicio"
        verbose_name_plural = "servicios"

    def __str__(self):
        return self.name


class AppointmentQuerySet(models.QuerySet):
    def visible_to(self, user):
        """El admin ve todas las citas; un cliente, solo las suyas."""
        appointments = self.select_related("client", "service")
        if user.is_admin:
            return appointments
        return appointments.filter(client=user)


class Appointment(models.Model):
    """Cita: une a un cliente con un servicio en una fecha (N-N con datos propios)."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        CONFIRMED = "confirmed", "Confirmada"
        CANCELLED = "cancelled", "Cancelada"

    # 1-N: si se borra el cliente, se borran sus citas (CASCADE).
    client = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="appointments", verbose_name="Cliente"
    )
    # 1-N: no se puede borrar un servicio que tiene citas (PROTECT).
    service = models.ForeignKey(
        Service, on_delete=models.PROTECT, related_name="appointments", verbose_name="Servicio"
    )
    date = models.DateField("Fecha")
    time = models.TimeField("Hora")
    status = models.CharField("Estado", max_length=10, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField("Notas", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AppointmentQuerySet.as_manager()

    class Meta:
        ordering = ["date", "time"]
        verbose_name = "cita"
        verbose_name_plural = "citas"
        constraints = [
            # Respaldo en la base de datos de la regla "no hay doble reserva"; el form la valida primero.
            models.UniqueConstraint(
                fields=["service", "date", "time"],
                condition=~Q(status="cancelled"),
                name="unique_active_appointment_slot",
            ),
        ]

    def __str__(self):
        return f"{self.service} - {self.date} {self.time:%H:%M}"

    def can_change_to(self, new_status, user):
        """Reglas de negocio: una cita cancelada es definitiva y solo un admin confirma."""
        if self.status == self.Status.CANCELLED:
            return False
        if new_status == self.Status.CANCELLED:
            return True
        return (
            new_status == self.Status.CONFIRMED
            and self.status == self.Status.PENDING
            and user.is_admin
        )
