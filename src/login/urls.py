from django.urls import path
from .views import *

app_name = 'auth'

urlpatterns = [
    # Autenticación
    path('login/', app_login, name="login"),
    path('registro/', app_registro, name="registro"),
    path('logout/', app_logout, name="logout"),
    path('denegado/', permission_denied, name="denegado"),
]