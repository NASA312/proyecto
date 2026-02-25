from datetime import datetime
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.http import require_http_methods
from .forms import LoginForm, RegistroUsuarioForm, EditarUsuarioForm, EditarPerfilForm
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from .forms import * 
from .models import *
from django.contrib import messages
from django.contrib.messages import get_messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import base64
import json
import requests

# ============================================
# FUNCIÓN AUXILIAR PARA VERIFICAR ADMIN
# ============================================

def es_admin(user):
    """Verifica si el usuario es superuser O tiene rol ADMIN"""
    if user.is_superuser:
        return True
    if hasattr(user, 'perfil') and user.perfil.rol:
        return user.perfil.rol.nombre == 'ADMIN'
    return False


# ============================================
# VISTAS DE AUTENTICACIÓN TRABAJADORES
# ============================================

def app_login(request):
    """Login solo para trabajadores del sistema"""
    if request.user.is_authenticated:
        return redirect('guarderia:dashboard')
    
    if request.method == "POST":
        usuario = request.POST.get('usuario')
        password = request.POST.get('contrasena')
        next_url = request.POST.get('next')
        
        user = authenticate(username=usuario.lower(), password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                # UN SOLO mensaje de bienvenida
                nombre = user.first_name or user.username
                messages.success(request, f'¡Bienvenido, {nombre}!')
                
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect('guarderia:dashboard')
            else:
                messages.error(request, 'Tu cuenta está desactivada.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    ctx = {
        'next': request.GET.get('next', '')
    }
    return render(request, "login/login.html", ctx)

@login_required
def app_logout(request):
    """Cerrar sesión y limpiar todos los mensajes"""
    # Limpiar TODOS los mensajes pendientes
    storage = get_messages(request)
    for _ in storage:
        pass  # Esto consume y elimina los mensajes
    
    # Ahora cerrar sesión
    logout(request)
    
    # NO agregar mensaje aquí para mantener el login limpio
    return redirect('auth:login')

def permission_denied(request):
    return render(request, "login/sin_permisos.html", {})


# ============================================
# VISTAS DE GESTIÓN DE USUARIOS
# ============================================

@login_required
def lista_usuarios(request):
    """Lista de todos los usuarios del sistema con tabs Activos/Papelera"""
    # ✅ Verificar si es ADMIN o Superuser
    if not es_admin(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('auth:denegado')
    
    usuarios_activos = User.objects.filter(is_active=True).select_related('perfil', 'perfil__rol').order_by('-date_joined')
    usuarios_inactivos = User.objects.filter(is_active=False).select_related('perfil', 'perfil__rol').order_by('-date_joined')
    
    ctx = {
        'usuarios_activos': usuarios_activos,
        'usuarios_inactivos': usuarios_inactivos,
        'total_usuarios': User.objects.count(),
    }
    return render(request, 'usuario/lista.html', ctx)


# ============================================
# FUNCIONES DE PAPELERA - USUARIOS
# ============================================

@login_required
@require_http_methods(["POST"])
def enviar_usuario_papelera(request, user_id):
    """Enviar usuario a papelera (marcar como inactivo)"""
    try:
        # ✅ Verificar permisos
        if not es_admin(request.user):
            return JsonResponse({
                'success': False,
                'message': 'No tienes permisos para realizar esta acción.'
            }, status=403)
        
        usuario = get_object_or_404(User, id=user_id)
        
        # ✅ No permitir desactivarse a sí mismo
        if usuario.id == request.user.id:
            return JsonResponse({
                'success': False,
                'message': 'No puedes desactivar tu propia cuenta.'
            }, status=400)
        
        # ✅ NUEVO: No permitir desactivar superusers
        if usuario.is_superuser:
            return JsonResponse({
                'success': False,
                'message': 'No se puede desactivar a un superadministrador del sistema.'
            }, status=400)
        
        # Enviar a papelera
        usuario.is_active = False
        usuario.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Usuario {usuario.username} enviado a papelera'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def restaurar_usuario(request, user_id):
    """Restaurar usuario desde papelera (marcar como activo)"""
    try:
        # ✅ Verificar permisos
        if not es_admin(request.user):
            return JsonResponse({
                'success': False,
                'message': 'No tienes permisos para realizar esta acción.'
            }, status=403)
        
        usuario = get_object_or_404(User, id=user_id)
        
        # Restaurar usuario
        usuario.is_active = True
        usuario.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Usuario {usuario.username} restaurado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


# ============================================
# OTRAS VISTAS DE USUARIOS
# ============================================

@login_required
def registrar_usuario(request):
    """Registrar nuevo usuario (solo administradores)"""
    # ✅ CORREGIDO: Permitir a ADMIN y Superuser
    if not es_admin(request.user):
        messages.error(request, 'No tienes permisos para registrar usuarios.')
        return redirect('auth:denegado')
    
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST, request.FILES)
        
        # Detectar si es petición AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            try:
                usuario = form.save()
                
                print(f"✅ Usuario {usuario.username} registrado exitosamente")
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': f'Usuario {usuario.username} registrado exitosamente.',
                        'redirect_url': '/auth/usuarios/'
                    })
                else:
                    messages.success(request, f'Usuario {usuario.username} registrado exitosamente.')
                    return redirect('auth:lista_usuarios')
                    
            except Exception as e:
                print(f"❌ ERROR AL GUARDAR: {str(e)}")
                
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': f'Error al guardar el usuario: {str(e)}'
                    }, status=500)
                else:
                    messages.error(request, f'Error al guardar el usuario: {str(e)}')
        else:
            if is_ajax:
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                return JsonResponse({
                    'success': False,
                    'errors': errors,
                    'message': 'Por favor corrige los errores en el formulario.'
                }, status=400)
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'usuario/registrar.html', {'form': form})


@login_required
def detalle_usuario(request, user_id):
    """Ver detalles de un usuario"""
    # ✅ Solo administradores o el mismo usuario pueden ver detalles
    if not es_admin(request.user) and request.user.id != user_id:
        messages.error(request, 'No tienes permisos para ver este usuario.')
        return redirect('auth:denegado')
    
    usuario = get_object_or_404(User, id=user_id)
    perfil = usuario.perfil
    
    ctx = {
        'usuario': usuario,
        'perfil': perfil,
    }
    return render(request, 'usuario/detalle.html', ctx)


@login_required
def editar_usuario(request, user_id):
    """Editar información de usuario"""
    # ✅ Solo administradores o el mismo usuario pueden editar
    if not es_admin(request.user) and request.user.id != user_id:
        messages.error(request, 'No tienes permisos para editar este usuario.')
        return redirect('auth:denegado')
    
    usuario = get_object_or_404(User, id=user_id)
    perfil = usuario.perfil
    
    if request.method == 'POST':
        user_form = EditarUsuarioForm(request.POST, instance=usuario)
        perfil_form = EditarPerfilForm(request.POST, request.FILES, instance=perfil)
        
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if user_form.is_valid() and perfil_form.is_valid():
            # Guardar usuario
            user_form.save()
            
            # Guardar perfil con campos adicionales
            perfil = perfil_form.save(commit=False)
            
            # Guardar foto de perfil si se subió
            if 'foto_perfil' in request.FILES:
                perfil.foto_perfil = request.FILES['foto_perfil']
            
            # Guardar fecha de nacimiento
            if request.POST.get('fecha_nacimiento'):
                perfil.fecha_nacimiento = request.POST.get('fecha_nacimiento')
            
            # Guardar dirección
            if request.POST.get('direccion'):
                perfil.direccion = request.POST.get('direccion')
            
            if request.POST.get('fecha_ingreso'):
                perfil.fecha_ingreso = request.POST.get('fecha_ingreso')
            perfil.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'Usuario {usuario.username} actualizado correctamente.',
                    'redirect_url': f'/auth/usuario/{usuario.id}/'
                })
            else:
                messages.success(request, f'Usuario {usuario.username} actualizado correctamente.')
                return redirect('auth:detalle_usuario', user_id=usuario.id)
        else:
            if is_ajax:
                errors = {}
                for field, error_list in user_form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                for field, error_list in perfil_form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                return JsonResponse({
                    'success': False,
                    'errors': errors,
                    'message': 'Por favor corrige los errores.'
                }, status=400)
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        user_form = EditarUsuarioForm(instance=usuario)
        perfil_form = EditarPerfilForm(instance=perfil)
    
    ctx = {
        'usuario': usuario,
        'perfil': perfil,
        'user_form': user_form,      
        'perfil_form': perfil_form,  
    }
    return render(request, 'usuario/editar.html', ctx)


@login_required
def desactivar_usuario(request, user_id):
    """Desactivar/Activar usuario (FUNCIÓN LEGACY - usar enviar_usuario_papelera)"""
    # ✅ Verificar permisos
    if not es_admin(request.user):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('auth:denegado')
    
    usuario = get_object_or_404(User, id=user_id)
    
    # ✅ No permitir desactivar al propio usuario
    if usuario.id == request.user.id:
        messages.error(request, 'No puedes desactivar tu propia cuenta.')
        return redirect('auth:lista_usuarios')
    
    # ✅ NUEVO: No permitir desactivar superusers
    if usuario.is_superuser:
        messages.error(request, 'No se puede desactivar a un superadministrador del sistema.')
        return redirect('auth:lista_usuarios')
    
    # Cambiar estado
    usuario.is_active = not usuario.is_active
    usuario.save()
    
    estado = "activado" if usuario.is_active else "desactivado"
    messages.success(request, f'Usuario {usuario.username} {estado} correctamente.')
    
    return redirect('auth:lista_usuarios')