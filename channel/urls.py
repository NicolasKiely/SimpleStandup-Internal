from django.urls import path

from channel import views

app_name = "channel"

urlpatterns = [
    path("create", views.create_channel, name="create"),
    path("list", views.list_channels, name="list"),
    path("members", views.get_channel_users, name="members"),
]
