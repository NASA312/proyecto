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
    
    # ============================================
    # Gestión de Usuarios (solo administradores)
    # ============================================
    path('usuarios/', lista_usuarios, name="lista_usuarios"),
    path('usuarios/registrar/', registrar_usuario, name="registrar_usuario"),
    
    # ========== PAPELERA USUARIOS ==========
    path('usuarios/<int:user_id>/enviar-papelera/', 
         enviar_usuario_papelera, 
         name='enviar_usuario_papelera'),
    
    path('usuarios/<int:user_id>/restaurar/', 
         restaurar_usuario, 
         name='restaurar_usuario'),
    
    # ========== OTRAS ACCIONES USUARIOS ==========
    path('usuarios/<int:user_id>/editar/', editar_usuario, name="editar_usuario"),
    path('usuarios/<int:user_id>/desactivar/', desactivar_usuario, name="desactivar_usuario"),
    path('usuarios/<int:user_id>/', detalle_usuario, name="detalle_usuario"),  # ← ESTA AL FINAL
]