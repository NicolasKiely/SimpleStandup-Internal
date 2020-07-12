from django.urls import path

from login import views

app_name = 'auth'

urlpatterns = [
    path(
        'user/register', views.register_user,
        name='register-user'
    ),
    path(
        'user/login', views.authenticate_user,
        name='authenticate-user'
    ),
    path(
        'user/settings/get', views.get_user_settings,
        name='get-user-settings'
    ),
]
