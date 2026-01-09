from datetime import datetime
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, authenticate, logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import * 
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def app_login(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            usuario = form.cleaned_data['usuario']
            password = form.cleaned_data['contrasena']
            next_url = request.POST.get('next')
            
            user = authenticate(username=usuario.lower(), password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Bienvenido {user.first_name or user.username}!')
                    
                    if next_url:
                        return redirect(next_url)
                    else:
                        return redirect('inicio')
                else:
                    messages.error(request, 'Tu cuenta está desactivada.')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = LoginForm()
    
    ctx = {
        'form': form,
        'next': request.GET.get('next', '')
    }
    return render(request, "login/login.html", ctx)

def app_registro(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, '¡Cuenta creada exitosamente! Ya puedes iniciar sesión.')
            return redirect('auth:login')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RegistroForm()
    
    ctx = {'form': form}
    return render(request, "login/registro.html", ctx)

def permission_denied(request):
    return render(request, "login/sin_permisos.html", {})

@login_required
def app_logout(request):
    logout(request)
    messages.info(request, 'Sesión cerrada exitosamente.')
    return redirect('auth:login')