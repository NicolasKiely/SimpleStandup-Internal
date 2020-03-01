from django.urls import path

from channel import views

app_name = "channel"

urlpatterns = [
    path("create", views.create_channel, name="create"),
]
