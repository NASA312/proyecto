from datetime import datetime
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, authenticate, logout
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from .forms import * 
from .models import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import base64
import json
import requests

# ============================================
# VISTAS DE AUTENTICACIÓN TRABAJADORES
# ============================================

def app_login(request):
    """Login solo para trabajadores del sistema"""
    if request.user.is_authenticated:
        return redirect('inicio')
    
    if request.method == "POST":
        usuario = request.POST.get('usuario')
        password = request.POST.get('contrasena')
        next_url = request.POST.get('next')
        
        user = authenticate(username=usuario.lower(), password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'¡Bienvenido {user.first_name or user.username}!')
                
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect('inicio')
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
    logout(request)
    messages.info(request, 'Sesión cerrada exitosamente.')
    return redirect('auth:login')

def permission_denied(request):
    return render(request, "login/sin_permisos.html", {})
