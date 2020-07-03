from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    """ Notification message for user """
    #: Message's target user
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)

    #: When message was created
    dt_created = models.DateTimeField(auto_now_add=True, null=False)

    #: Message title
    title = models.CharField(max_length=4096, null=False)

    #: Message to display
    message = models.CharField(max_length=4096, null=False)

    #: Type of notification
    role = models.CharField(max_length=16, null=False, default="")

    #: Flag set if notification has been dismissed
    dismissed = models.BooleanField(null=False, default=False)
