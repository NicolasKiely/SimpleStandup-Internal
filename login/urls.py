from django.urls import path

from login import views

app_name = 'auth'

urlpatterns = [
    path(
        'user/register', views.register_user,
        name='register-user'
    ),
]
