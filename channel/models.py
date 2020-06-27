from django.db import models
from django.contrib.auth.models import User


class Channel(models.Model):
    """ Channel owned by user """
    #: Owner of channel
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    #: Name of channel
    name = models.CharField(max_length=64)

    #: Soft delete
    archived = models.BooleanField(default=False)

    class Meta:
        unique_together = ("owner", "name")


class ChannelMember(models.Model):
    """ Channel membership relation. Unique per user and channel """
    #: User in channel
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)

    #: Channel
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, null=False)

    #: Optional descriptive role of user in channel
    role = models.CharField(max_length=32, default="", null=False)

    #: Date joined
    dt_joined = models.DateTimeField(auto_now_add=True, null=False)

    #: If user has moderator control over channel
    is_mod = models.BooleanField(default=False, null=False)

    class Meta:
        unique_together = ("user", "channel")
