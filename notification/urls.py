from django.urls import path

from notification import views

app_name = "notification"

urlpatterns = [
    path("list/unread", views.get_unread_notifications, name="get-unread"),
    path("response", views.handle_notification_response, name="response")
]
