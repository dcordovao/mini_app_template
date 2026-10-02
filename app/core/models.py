from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Service(models.Model):
    name = models.CharField(max_length= 50)
    price = models.IntegerField()
    description = models.CharField(max_length= 100, default = "Soy un servicio")
    def __str__(self):
        return self.name

    