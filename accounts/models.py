from django.contrib.auth.models import AbstractUser
from django.db import models


class role(models.Model):
    name = models.CharField(max_length=10)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name




class CustomUser(AbstractUser):
    role = models.ForeignKey('role', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.username
