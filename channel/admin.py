from django.contrib import admin

from channel import models

# Register your models here.
admin.site.register(models.Channel)
admin.site.register(models.ChannelMember)
admin.site.register(models.ChannelMessage)
