from django.urls import path
from .views import *

app_name = 'auth'

urlpatterns = [
    # ============================================
    # Autenticación de Trabajadores
    # ============================================
    path('login/', app_login, name="login"),
    path('logout/', app_logout, name="logout"),
    path('denegado/', permission_denied, name="denegado"),
    
]