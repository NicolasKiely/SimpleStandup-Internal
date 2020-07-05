from django.db import models
from django.contrib.auth.models import User

import notification.models


class Channel(models.Model):
    """ Channel owned by user """
    #: Owner of channel
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    #: Name of channel
    name = models.CharField(max_length=64)

    #: Soft delete
    archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name

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

    def __str__(self):
        return "%s: %s" % (self.channel.name, self.user.email)

    class Meta:
        unique_together = ("user", "channel")


class ChannelInvite(models.Model):
    """ Invitation for user to channel """
    #: Associated notification message for invite
    note = models.OneToOneField(
        notification.models.Notification, on_delete=models.CASCADE
    )

    #: User of invite
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)

    #: Channel user is invited to
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, null=False)

    def __str__(self):
        return "%s: %s" % (self.channel.name, self.user.email)

    class Meta:
        unique_together = ("user", "channel")


class ChannelMessage(models.Model):
    """ Message posted to channel """
    #: Date posted
    dt_posted = models.DateField(null=False)

    #: Message body posted
    message = models.CharField(max_length=4096)

    #: Author of message
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)

    #: Message's channel
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, null=False)

    def __str__(self):
        return "[%s] %s %s: %s" % (
            self.channel.name, self.dt_posted, self.user.email, self.message
        )

    class Meta:
        unique_together = ("user", "channel", "dt_posted")
