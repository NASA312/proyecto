from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

# ============================================
# DECORADOR LEGACY (GRUPOS DE DJANGO)
# ============================================

def group_required(*group_names):
    """Requires user membership in at least one of the groups passed in."""
    def in_groups(u):
        if u.is_authenticated:
            if bool(u.groups.filter(name__in=group_names)) | u.is_superuser:
                return True
        return False

    return user_passes_test(in_groups, login_url='/auth/denegado', redirect_field_name=None)


# ============================================
# FUNCIONES AUXILIARES
# ============================================

def es_admin(user):
    """Verifica si el usuario es superuser O tiene rol ADMIN"""
    if user.is_superuser:
        return True
    if hasattr(user, 'perfil') and user.perfil.rol:
        return user.perfil.rol.nombre == 'ADMIN'
    return False


def es_empleado(user):
    """Verifica si el usuario tiene rol EMPLEADO"""
    if user.is_superuser:
        return True
    if hasattr(user, 'perfil') and user.perfil.rol:
        return user.perfil.rol.nombre == 'EMPLEADO'
    return False


def es_observador(user):
    """Verifica si el usuario tiene rol OBSERVADOR"""
    if hasattr(user, 'perfil') and user.perfil.rol:
        return user.perfil.rol.nombre == 'OBSERVADOR'
    return False


def tiene_rol(user, *roles_permitidos):
    """
    Verifica si el usuario tiene uno de los roles permitidos
    Args:
        user: Usuario de Django
        *roles_permitidos: Lista de roles como strings ('ADMIN', 'EMPLEADO', 'OBSERVADOR')
    Returns:
        bool: True si el usuario tiene uno de los roles permitidos
    """
    # Superuser siempre tiene acceso
    if user.is_superuser:
        return True
    
    # Verificar si tiene perfil y rol
    if hasattr(user, 'perfil') and user.perfil.rol:
        return user.perfil.rol.nombre in roles_permitidos
    
    return False


# ============================================
# DECORADORES POR ROL ESPECÍFICO
# ============================================

def admin_requerido(view_func):
    """
    Decorador que requiere que el usuario sea ADMIN o Superuser
    Uso: @admin_requerido
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if es_admin(request.user):
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'Solo los administradores pueden acceder a esta página.')
        return redirect('auth:denegado')
    
    return wrapper


def empleado_requerido(view_func):
    """
    Decorador que requiere que el usuario sea EMPLEADO, ADMIN o Superuser
    Uso: @empleado_requerido
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if es_admin(request.user) or es_empleado(request.user):
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'Solo empleados y administradores pueden acceder a esta página.')
        return redirect('auth:denegado')
    
    return wrapper


# ============================================
# DECORADOR GENÉRICO POR ROLES
# ============================================

def rol_requerido(*roles_permitidos):
    """
    Decorador genérico para proteger vistas por rol
    
    Uso:
        @rol_requerido('ADMIN')
        @rol_requerido('ADMIN', 'EMPLEADO')
        @rol_requerido('ADMIN', 'EMPLEADO', 'OBSERVADOR')
    
    Args:
        *roles_permitidos: Nombres de roles permitidos como strings
    
    Returns:
        Decorador que verifica si el usuario tiene uno de los roles permitidos
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Superuser siempre puede acceder
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verificar si tiene perfil y rol
            if hasattr(request.user, 'perfil') and request.user.perfil.rol:
                if request.user.perfil.rol.nombre in roles_permitidos:
                    return view_func(request, *args, **kwargs)
            
            # Sin permisos
            roles_texto = ' o '.join(roles_permitidos)
            messages.error(request, f'Esta página requiere rol: {roles_texto}')
            return redirect('auth:denegado')
        
        return wrapper
    return decorator


# ============================================
# DECORADOR PARA AJAX
# ============================================

def rol_requerido_ajax(*roles_permitidos):
    """
    Decorador para vistas AJAX que requieren roles específicos
    Retorna JsonResponse en lugar de redirect
    
    Uso: @rol_requerido_ajax('ADMIN', 'EMPLEADO')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from django.http import JsonResponse
            
            # Superuser siempre puede acceder
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verificar si tiene perfil y rol
            if hasattr(request.user, 'perfil') and request.user.perfil.rol:
                if request.user.perfil.rol.nombre in roles_permitidos:
                    return view_func(request, *args, **kwargs)
            
            # Sin permisos - retornar JSON
            return JsonResponse({
                'success': False,
                'message': 'No tienes permisos para realizar esta acción.'
            }, status=403)
        
        return wrapper
    return decorator


# ============================================
# VERIFICACIÓN EN TEMPLATES
# ============================================

def puede_editar(user, objeto=None):
    """
    Verifica si el usuario puede editar un objeto
    Para usar en templates: {% if puede_editar(request.user, objeto) %}
    """
    # Admin siempre puede editar
    if es_admin(user):
        return True
    
    # Empleado puede editar la mayoría de cosas
    if es_empleado(user):
        # Si es un usuario, solo puede editar su propio perfil
        if hasattr(objeto, 'username'):  # Es un User
            return objeto.id == user.id
        return True
    
    # Observador solo puede editar observaciones que creó
    if es_observador(user):
        if hasattr(objeto, 'registrado_por'):  # Es una Observación
            return objeto.registrado_por == user
        return False
    
    return False


def puede_eliminar(user, objeto=None):
    """
    Verifica si el usuario puede eliminar un objeto
    """
    # Solo Admin puede eliminar
    return es_admin(user)