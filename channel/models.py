from django.db import models
from django.contrib.auth.models import User


class Channel(models.Model):
    """ Channel owned by user """
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=64)
    archived = models.BooleanField(default=False)

    class Meta:
        unique_together = ("owner", "name")
