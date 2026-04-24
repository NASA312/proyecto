from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import subprocess
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.utils import timezone
import shutil
from datetime import datetime, timedelta
from .models import Tutor, Nino, RegistroAcceso
from .forms import *
import base64
import json
import requests
from django.db.models import Count, Q
import requests
from django.views.decorators.http import require_http_methods
from django.conf import settings
import pandas as pd
import os
from django.db import transaction 

# ============================================
# IMPORTAR DECORADORES DE PERMISOS
# ============================================
from login.decorators import rol_requerido, admin_requerido

# ============================================
# VISTAS DE TUTORES
# ============================================

@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
def lista_tutores(request):
    """Lista de tutores registrados"""
    tutores_activos   = Tutor.objects.filter(activo=True).order_by('-fecha_registro')
    tutores_inactivos = Tutor.objects.filter(activo=False).order_by('-fecha_registro')
    return render(request, 'guarderia/tutores/lista.html', {
        'tutores_activos':   tutores_activos,
        'tutores_inactivos': tutores_inactivos,
    })


@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
def registrar_tutor(request):
    """Registrar nuevo tutor"""
    if request.method == 'POST':
        # ✅ CORRECCIÓN: Hacer una copia mutable del POST data
        post_data = request.POST.copy()
        
        # ✅ Si NO es trabajador, limpiar campos laborales para evitar errores de validación
        if not post_data.get('es_trabajador'):
            post_data['dependencia'] = ''
            post_data['departamento'] = ''
            post_data['estatus_laboral'] = ''
            post_data['numero_empleado'] = ''
            post_data['fecha_alta'] = ''
            post_data['fecha_baja'] = ''
        
        # Crear el formulario con los datos modificados
        form = TutorForm(post_data)
        
        # Detectar si es petición AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            tutor = form.save(commit=False)
            tutor.activo = True    # ← siempre activo al crear
            tutor.save()
            form.save_m2m()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'Tutor {tutor.nombre_completo()} registrado exitosamente',
                    'redirect_url': f'/guarderia/tutores/{tutor.id}/huella/'
                })
            else:
                messages.success(request, f'Tutor {tutor.nombre_completo()} registrado. Ahora registra su huella.')
                return redirect('guarderia:registrar_huella_tutor', tutor_id=tutor.id)
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
        form = TutorForm()
    
    return render(request, 'guarderia/tutores/registrar.html', {'form': form})

@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
def detalle_tutor(request, tutor_id):
    """Ver detalles de un tutor"""
    tutor = get_object_or_404(Tutor, id=tutor_id)
    ninos = tutor.ninos.filter(activo=True)
    registros = tutor.registros.all().order_by('-fecha_hora')[:10]
    
    ctx = {
        'tutor': tutor,
        'ninos': ninos,
        'registros': registros
    }
    return render(request, 'guarderia/tutores/detalle.html', ctx)

@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
def editar_tutor(request, tutor_id):
    """Editar información de tutor"""
    tutor = get_object_or_404(Tutor, id=tutor_id)
    
    if request.method == 'POST':
        form = TutorForm(request.POST, instance=tutor)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            form.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'Tutor {tutor.nombre_completo()} actualizado correctamente.',
                    'redirect_url': f'/guarderia/tutores/{tutor.id}/'
                })
            else:
                messages.success(request, f'Tutor {tutor.nombre_completo()} actualizado correctamente.')
                return redirect('guarderia:detalle_tutor', tutor_id=tutor.id)
        else:
            if is_ajax:
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                return JsonResponse({
                    'success': False,
                    'errors': errors,
                    'message': 'Por favor corrige los errores.'
                }, status=400)
    else:
        form = TutorForm(instance=tutor)
    
    # Pasar datos de la colonia si existe
    context = {
        'form': form,
        'tutor': tutor,
    }
    
    # Si tiene colonia, pasarla al contexto
    if tutor.colonia:
        context['colonia_actual'] = {
            'id': tutor.colonia.id,
            'nombre': tutor.colonia.d_asenta,
            'municipio': tutor.colonia.D_mnpio,
            'estado': tutor.colonia.d_estado,
        }
    
    return render(request, 'guarderia/tutores/editar.html', context)

@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
def registrar_huella_tutor(request, tutor_id):
    """Registrar huella del tutor con lector biométrico"""
    tutor = get_object_or_404(Tutor, id=tutor_id)
    
    # Enviar solicitud al servidor .NET para iniciar captura
    if request.method == 'GET' and not tutor.huella_registrada:
        try:
            response = requests.get(
                f'http://localhost:5000/capturar?persona_id={tutor_id}&tipo=tutor',
                timeout=2
            )
            print(f"✓ Solicitud enviada al servidor biométrico para tutor {tutor_id}")
            print(f"Respuesta del servidor .NET: {response.json()}")
        except requests.exceptions.ConnectionError:
            messages.error(request, 'No se puede conectar con el lector de huellas.')
        except Exception as e:
            print(f"✗ Error: {e}")
    
    return render(request, 'guarderia/tutores/registrar_huella.html', {'tutor': tutor})

# ============================================
# VISTAS DE NIÑOS
# ============================================

@login_required
def lista_ninos(request):
    """Lista de niños registrados"""
    ninos_activos   = Nino.objects.filter(activo=True).order_by('grupo', 'apellido_paterno')
    ninos_inactivos = Nino.objects.filter(activo=False).order_by('grupo', 'apellido_paterno')
    return render(request, 'guarderia/ninos/lista.html', {
        'ninos_activos':   ninos_activos,
        'ninos_inactivos': ninos_inactivos,
    })

@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
def registrar_nino(request):
    """Registrar nuevo niño"""
    if request.method == 'POST':
        form = NinoForm(request.POST, request.FILES)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            nino = form.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'Niño {nino.nombre_completo()} registrado exitosamente.',
                    'redirect_url': f'/guarderia/ninos/{nino.id}/asignar-tutores/'
                })
            else:
                messages.success(request, f'Niño {nino} registrado exitosamente.')
                return redirect('guarderia:asignar_tutores', nino_id=nino.id)
        else:
            if is_ajax:
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                return JsonResponse({
                    'success': False,
                    'errors': errors,
                    'message': 'Por favor corrige los errores.'
                }, status=400)
            else:
                messages.error(request, 'Por favor corrige los errores.')
    else:
        form = NinoForm()
    
    return render(request, 'guarderia/ninos/registrar.html', {'form': form})

@login_required
def detalle_nino(request, nino_id):
    """Ver detalles de un niño"""
    nino = get_object_or_404(Nino, id=nino_id)
    tutores = nino.tutores.filter(activo=True)
    registros = nino.registros.all().order_by('-fecha_hora')[:10]
    observaciones = nino.observaciones.select_related('registrado_por').order_by('-fecha', '-hora')[:10]

    ctx = {
        'nino': nino,
        'tutores': tutores,
        'registros': registros,
        'observaciones': observaciones,  # <-- nuevo
    }
    return render(request, 'guarderia/ninos/detalle.html', ctx)

@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
def editar_nino(request, nino_id):
    """Editar información de niño"""
    nino = get_object_or_404(Nino, id=nino_id)
    
    if request.method == 'POST':
        form = NinoForm(request.POST, request.FILES, instance=nino)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            form.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'Niño {nino.nombre_completo()} actualizado correctamente.',
                    'redirect_url': f'/guarderia/ninos/{nino.id}/'
                })
            else:
                messages.success(request, f'Niño {nino.nombre_completo()} actualizado correctamente.')
                return redirect('guarderia:detalle_nino', nino_id=nino.id)
        else:
            if is_ajax:
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                return JsonResponse({
                    'success': False,
                    'errors': errors,
                    'message': 'Por favor corrige los errores.'
                }, status=400)
    else:
        form = NinoForm(instance=nino)
    
    return render(request, 'guarderia/ninos/editar.html', {'form': form, 'nino': nino})

@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
def asignar_tutores(request, nino_id):
    """Asignar tutores a un niño"""
    nino = get_object_or_404(Nino, id=nino_id)
    
    if request.method == 'POST':
        form = AsignarTutorForm(request.POST)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            nino.tutores.set(form.cleaned_data['tutores'])
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'Tutores asignados a {nino.nombre_completo()}',
                    'redirect_url': f'/guarderia/ninos/{nino.id}/'
                })
            else:
                messages.success(request, f'Tutores asignados a {nino}')
                return redirect('guarderia:detalle_nino', nino_id=nino.id)
        else:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': 'Error al asignar tutores.'
                }, status=400)
    else:
        form = AsignarTutorForm(initial={'tutores': nino.tutores.all()})
    
    return render(request, 'guarderia/ninos/asignar_tutores.html', {
        'form': form,
        'nino': nino
    })

# ============================================
# VISTAS DE VERIFICACIÓN (PÚBLICAS)
# ============================================

def verificar_huella_tutor(request):
    """Vista pública para verificar huella de tutor"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            huella_template = data.get('huella_template')
            
            if huella_template:
                template_recibido = base64.b64decode(huella_template)
                
                tutor = Tutor.objects.filter(
                    huella_template=template_recibido,
                    huella_registrada=True,
                    activo=True
                ).first()
                
                if tutor:
                    ninos = tutor.ninos.filter(activo=True)
                    ninos_data = [{
                        'id': nino.id,
                        'nombre': nino.nombre_completo(),
                        'grupo': nino.grupo,
                        'edad': nino.edad()
                    } for nino in ninos]
                    
                    return JsonResponse({
                        'success': True,
                        'tutor': {
                            'id': tutor.id,
                            'nombre': tutor.nombre_completo(),
                            'parentesco': tutor.get_parentesco_display(),
                            'telefono': tutor.telefono
                        },
                        'ninos': ninos_data
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'mensaje': 'Huella no reconocida'
                    })
        except Exception as e:
            return JsonResponse({'success': False, 'mensaje': str(e)})
    
    return render(request, 'guarderia/verificar_huella.html')

# ============================================
# VISTAS DE REGISTROS
# ============================================

@login_required
@rol_requerido('ADMIN', 'EMPLEADO', 'OBSERVADOR')
def historial_accesos(request):
    """Historial de entradas y salidas con filtros avanzados"""
    
    # Obtener parámetros de filtro
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    nino_id = request.GET.get('nino', '')
    tutor_id = request.GET.get('tutor', '')
    tipo = request.GET.get('tipo', '')  # ENTRADA o SALIDA
    grupo_id = request.GET.get('grupo', '')
    
    # Query base
    registros = RegistroAcceso.objects.select_related(
        'nino', 
        'tutor', 
        'nino__grupo'
    )
    
    # ⚠️ APLICAR TODOS LOS FILTROS ANTES DEL SLICE
    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            registros = registros.filter(fecha_hora__date__gte=fecha_desde_obj)
        except ValueError:
            messages.warning(request, 'Formato de fecha desde inválido')
    
    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            registros = registros.filter(fecha_hora__date__lte=fecha_hasta_obj)
        except ValueError:
            messages.warning(request, 'Formato de fecha hasta inválido')
    
    if nino_id:
        registros = registros.filter(nino_id=nino_id)
    
    if tutor_id:
        registros = registros.filter(tutor_id=tutor_id)
    
    if tipo:
        registros = registros.filter(tipo=tipo)
    
    if grupo_id:
        registros = registros.filter(nino__grupo_id=grupo_id)
    
    # ⚠️ CALCULAR ESTADÍSTICAS ANTES DEL SLICE
    total_registros = registros.count()
    entradas = registros.filter(tipo='ENTRADA').count()
    salidas = registros.filter(tipo='SALIDA').count()
    
    # ⚠️ APLICAR ORDER BY Y SLICE AL FINAL
    registros = registros.order_by('-fecha_hora')[:500]
    
    # Datos para los select de filtros
    ninos = Nino.objects.filter(activo=True).order_by('apellido_paterno', 'nombre')
    tutores = Tutor.objects.filter(activo=True).order_by('apellido_paterno', 'nombre')
    grupos = Grupo.objects.filter(activo=True).order_by('tipo', 'grado', 'nombre')
    
    # Calcular cuáles de los registros son la ENTRADA actual (activa)
    entradas_activas_ids = set()
    ninos_verificados = set()
    for reg in registros:
        if reg.nino_id not in ninos_verificados:
            if reg.tipo == 'ENTRADA':
                # Verificar si realmente es el último registro absoluto del niño
                ultimo = RegistroAcceso.objects.filter(nino_id=reg.nino_id).order_by('-fecha_hora').first()
                if ultimo and ultimo.id == reg.id:
                    entradas_activas_ids.add(reg.id)
            ninos_verificados.add(reg.nino_id)
    
    context = {
        'registros': registros,
        'ninos': ninos,
        'tutores': tutores,
        'grupos': grupos,
        'tipo_choices': RegistroAcceso.TIPO_CHOICES,
        'entradas_activas_ids': entradas_activas_ids,
        
        # Estadísticas
        'total_registros': total_registros,
        'entradas': entradas,
        'salidas': salidas,
        
        # Mantener valores de filtros
        'filtro_fecha_desde': fecha_desde,
        'filtro_fecha_hasta': fecha_hasta,
        'filtro_nino': nino_id,
        'filtro_tutor': tutor_id,
        'filtro_tipo': tipo,
        'filtro_grupo': grupo_id,
    }
    
    return render(request, 'guarderia/registros/historial.html', context)

# Agregar esta nueva función en views.py

@csrf_exempt  
def registrar_entrada(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nino_id   = data.get('nino_id')
            tutor_id  = data.get('tutor_id')
            observaciones = data.get('observaciones', '').strip()
            
            if not nino_id or not tutor_id:
                return JsonResponse({'success': False, 'mensaje': 'Faltan datos'}, status=400)
            
            nino  = Nino.objects.get(id=nino_id, activo=True)
            tutor = Tutor.objects.get(id=tutor_id, activo=True)
            
            # Verificar autorización
            if tutor not in nino.tutores.all():
                return JsonResponse({
                    'success': False,
                    'mensaje': f'{tutor.nombre_completo()} no está autorizado para este niño'
                }, status=403)
            
            # ── Validación de tiempo mínimo ──────────────────────────
            config = ConfiguracionGuarderia.get_solo()
            minutos_minimo = config.tiempo_minimo_entre_registros
            
            ultimo_registro = RegistroAcceso.objects.filter(
                nino=nino
            ).order_by('-fecha_hora').first()
            
            if ultimo_registro:
                delta = timezone.now() - ultimo_registro.fecha_hora
                minutos_transcurridos = delta.total_seconds() / 60
                
                if minutos_transcurridos < minutos_minimo:
                    faltan = minutos_minimo - minutos_transcurridos
                    minutos_faltan = int(faltan)
                    segundos_faltan = int((faltan - minutos_faltan) * 60)
                    
                    tipo_anterior = 'entrada' if ultimo_registro.tipo == 'ENTRADA' else 'salida'
                    return JsonResponse({
                        'success': False,
                        'tiempo_bloqueado': True,
                        'mensaje': (
                            f'Debe esperar {minutos_faltan}m {segundos_faltan}s más. '
                            f'El último registro ({tipo_anterior}) fue hace '
                            f'{int(minutos_transcurridos)}m {int((minutos_transcurridos % 1) * 60)}s. '
                            f'El tiempo mínimo entre registros es {minutos_minimo} minutos.'
                        )
                    }, status=400)
            # ── Fin validación de tiempo ─────────────────────────────
            
            # Verificar si ya hay una entrada sin salida
            ultima_entrada = RegistroAcceso.objects.filter(
                nino=nino, tipo='ENTRADA'
            ).order_by('-fecha_hora').first()
            
            if ultima_entrada:
                salida_posterior = RegistroAcceso.objects.filter(
                    nino=nino, tipo='SALIDA',
                    fecha_hora__gt=ultima_entrada.fecha_hora
                ).exists()
                
                if not salida_posterior:
                    return JsonResponse({
                        'success': False,
                        'mensaje': f'{nino.nombre_completo()} ya tiene una entrada registrada sin salida.'
                    }, status=400)
            
            registro = RegistroAcceso.objects.create(
                nino=nino, tutor=tutor, tipo='ENTRADA',
                verificacion_exitosa=True, metodo_verificacion='HUELLA',
                observaciones=observaciones if observaciones else None
            )
            
            return JsonResponse({
                'success': True,
                'mensaje': f'{nino.nombre_completo()} ingresado por {tutor.nombre_completo()}',
                'registro_id': registro.id
            })
            
        except Nino.DoesNotExist:
            return JsonResponse({'success': False, 'mensaje': 'Niño no encontrado'}, status=404)
        except Tutor.DoesNotExist:
            return JsonResponse({'success': False, 'mensaje': 'Tutor no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'mensaje': f'Error: {str(e)}'}, status=500)
    
    return JsonResponse({'success': False}, status=405)



# MODIFICAR la función registrar_salida existente para agregar validaciones

@csrf_exempt  
def registrar_salida(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nino_id   = data.get('nino_id')
            tutor_id  = data.get('tutor_id')
            observaciones = data.get('observaciones', '').strip()
            
            if not nino_id or not tutor_id:
                return JsonResponse({'success': False, 'mensaje': 'Faltan datos'}, status=400)
            
            nino  = Nino.objects.get(id=nino_id, activo=True)
            tutor = Tutor.objects.get(id=tutor_id, activo=True)
            
            # Verificar autorización
            if tutor not in nino.tutores.all():
                return JsonResponse({
                    'success': False,
                    'mensaje': f'{tutor.nombre_completo()} no está autorizado para recoger a {nino.nombre_completo()}'
                }, status=403)
            
            # ── Validación de tiempo mínimo ──────────────────────────
            config = ConfiguracionGuarderia.get_solo()
            minutos_minimo = config.tiempo_minimo_entre_registros
            
            ultimo_registro = RegistroAcceso.objects.filter(
                nino=nino
            ).order_by('-fecha_hora').first()
            
            if ultimo_registro:
                delta = timezone.now() - ultimo_registro.fecha_hora
                minutos_transcurridos = delta.total_seconds() / 60
                
                if minutos_transcurridos < minutos_minimo:
                    faltan = minutos_minimo - minutos_transcurridos
                    minutos_faltan = int(faltan)
                    segundos_faltan = int((faltan - minutos_faltan) * 60)
                    
                    tipo_anterior = 'entrada' if ultimo_registro.tipo == 'ENTRADA' else 'salida'
                    return JsonResponse({
                        'success': False,
                        'tiempo_bloqueado': True,
                        'mensaje': (
                            f'Debe esperar {minutos_faltan}m {segundos_faltan}s más. '
                            f'El último registro ({tipo_anterior}) fue hace '
                            f'{int(minutos_transcurridos)}m {int((minutos_transcurridos % 1) * 60)}s. '
                            f'El tiempo mínimo entre registros es {minutos_minimo} minutos.'
                        )
                    }, status=400)
            # ── Fin validación de tiempo ─────────────────────────────
            
            # Verificar si hay una entrada previa
            ultima_entrada = RegistroAcceso.objects.filter(
                nino=nino, tipo='ENTRADA'
            ).order_by('-fecha_hora').first()
            
            if ultima_entrada:
                salida_posterior = RegistroAcceso.objects.filter(
                    nino=nino, tipo='SALIDA',
                    fecha_hora__gt=ultima_entrada.fecha_hora
                ).exists()
                
                if salida_posterior:
                    return JsonResponse({
                        'success': False,
                        'mensaje': f'{nino.nombre_completo()} ya tiene una salida registrada.'
                    }, status=400)
            else:
                observaciones = (observaciones + ' | ' if observaciones else '') + 'SALIDA SIN ENTRADA PREVIA REGISTRADA'
            
            registro = RegistroAcceso.objects.create(
                nino=nino, tutor=tutor, tipo='SALIDA',
                verificacion_exitosa=True, metodo_verificacion='HUELLA',
                observaciones=observaciones if observaciones else None
            )
            
            return JsonResponse({
                'success': True,
                'mensaje': f'{nino.nombre_completo()} entregado a {tutor.nombre_completo()}',
                'registro_id': registro.id
            })
            
        except Nino.DoesNotExist:
            return JsonResponse({'success': False, 'mensaje': 'Niño no encontrado'}, status=404)
        except Tutor.DoesNotExist:
            return JsonResponse({'success': False, 'mensaje': 'Tutor no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'mensaje': f'Error: {str(e)}'}, status=500)
    
    return JsonResponse({'success': False}, status=405)


# ============================================
# REEMPLAZAR la función obtener_estado_nino en guarderia/views.py
# (Está alrededor de la línea 500)
# ============================================

@csrf_exempt  # Agregar esto si no lo tiene
def obtener_estado_nino(request, nino_id):
    """
    Obtener el estado actual de un niño (DENTRO o FUERA)
    Lógica corregida
    """
    try:
        nino = Nino.objects.get(id=nino_id, activo=True)
        
        # Buscar la última ENTRADA
        ultima_entrada = RegistroAcceso.objects.filter(
            nino=nino,
            tipo='ENTRADA'
        ).order_by('-fecha_hora').first()
        
        # Si NO tiene ninguna entrada → está FUERA
        if not ultima_entrada:
            return JsonResponse({
                'success': True,
                'nino_id': nino.id,
                'nombre': nino.nombre_completo(),
                'estado': 'FUERA',
                'ultimo_registro': None
            })
        
        # Buscar si hay SALIDA después de la última entrada
        salida_posterior = RegistroAcceso.objects.filter(
            nino=nino,
            tipo='SALIDA',
            fecha_hora__gt=ultima_entrada.fecha_hora
        ).order_by('-fecha_hora').first()
        
        # Si hay salida posterior → está FUERA
        # Si NO hay salida posterior → está DENTRO
        if salida_posterior:
            estado = 'FUERA'
            ultimo = salida_posterior
        else:
            estado = 'DENTRO'
            ultimo = ultima_entrada
        
        return JsonResponse({
            'success': True,
            'nino_id': nino.id,
            'nombre': nino.nombre_completo(),
            'estado': estado,
            'ultimo_registro': {
                'tipo': ultimo.tipo,
                'fecha_hora': ultimo.fecha_hora.isoformat(),
                'tutor': ultimo.tutor.nombre_completo()
            }
        })
        
    except Nino.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Niño no encontrado'
        }, status=404)
    except Exception as e:
        print(f"❌ Error en obtener_estado_nino: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ============================================
# APIs para .NET - MÉTODO DE CONSULTA
# ============================================

def buscar_nino_por_matricula(request):
    matricula = request.GET.get('matricula', '').strip()

    if not matricula:
        return JsonResponse({'success': False, 'mensaje': 'Ingrese una matrícula.'})

    try:
        nino = Nino.objects.get(numero_matricula=matricula, activo=True)
    except Nino.DoesNotExist:
        return JsonResponse({'success': False, 'mensaje': 'No se encontró ningún niño con esa matrícula.'})

    ultimo = RegistroAcceso.objects.filter(nino=nino).order_by('-fecha_hora').first()
    estado = 'DENTRO' if (ultimo and ultimo.tipo == 'ENTRADA') else 'FUERA'

    return JsonResponse({
        'success': True,
        'nino': {
            'id':       nino.id,
            'nombre':   nino.nombre_completo(),
            'grupo':    str(nino.grupo),
            'edad':     nino.edad(),        # <-- agregar ()
            'foto_url': nino.foto.url if nino.foto else None,
            'estado':   estado,
        }
    })

@csrf_exempt
def verificar_huella_capturada_tutor(request, tutor_id):
    """API para verificar si la huella ya fue capturada - Consulta al servidor .NET"""
    print(f"\n🔍 Verificando captura para tutor {tutor_id}")
    
    try:
        # Consultar estado al servidor .NET (puerto 5000)
        response = requests.get(f'http://localhost:5000/estado', timeout=2)
        data = response.json()
        
        print(f"📡 Respuesta del servidor .NET:")
        print(f"   - completado: {data.get('completado')}")
        print(f"   - persona_id: {data.get('persona_id')}")
        print(f"   - tiene imagen: {'Sí' if data.get('huella_imagen') else 'No'}")
        print(f"   - tiene template: {'Sí' if data.get('huella_template') else 'No'}")
        
        # Si la captura está completa Y es para este tutor
        if data.get('completado') and str(data.get('persona_id')) == str(tutor_id):
            print(f"✅ Huella completada para tutor {tutor_id}")
            tutor = Tutor.objects.get(id=tutor_id)
            
            # Guardar imagen
            if data.get('huella_imagen'):
                try:
                    imagen_data = base64.b64decode(data['huella_imagen'])
                    tutor.huella_imagen.save(
                        f'tutor_{tutor.id}.png',
                        ContentFile(imagen_data),
                        save=False
                    )
                    print(f"✅ Imagen guardada: {tutor.huella_imagen.name}")
                except Exception as e:
                    print(f"❌ Error guardando imagen: {e}")
            
            # Guardar template
            if data.get('huella_template'):
                try:
                    tutor.huella_template = base64.b64decode(data['huella_template'])
                    print(f"✅ Template guardado: {len(tutor.huella_template)} bytes")
                except Exception as e:
                    print(f"❌ Error guardando template: {e}")
            
            # Marcar como registrada
            tutor.huella_registrada = True
            tutor.fecha_registro_huella = timezone.now()
            tutor.save()
            
            print(f"💾 Guardado en BD - huella_registrada: {tutor.huella_registrada}")
            print("="*50)
            print("✅ HUELLA REGISTRADA EXITOSAMENTE EN DJANGO")
            print("="*50 + "\n")
            
            return JsonResponse({
                'capturada': True,
                'imagen_url': tutor.huella_imagen.url if tutor.huella_imagen else None,
                'huella_registrada': tutor.huella_registrada
            })
        else:
            print(f"⏳ Aún no completado o persona_id no coincide")
            return JsonResponse({'capturada': False})
            
    except requests.exceptions.ConnectionError:
        print(f"❌ No se pudo conectar al servidor .NET en localhost:5000")
        return JsonResponse({
            'capturada': False, 
            'error': 'Servidor .NET no disponible'
        })
    except Tutor.DoesNotExist:
        print(f"❌ Tutor {tutor_id} no encontrado en la BD")
        return JsonResponse({'error': 'Tutor no encontrado'}, status=404)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'capturada': False, 
            'error': str(e)
        })

@login_required
def verificar_estado_huella(request, tutor_id):
    """Endpoint para verificar el estado de la huella en la BD"""
    try:
        tutor = Tutor.objects.get(id=tutor_id)
        
        return JsonResponse({
            'success': True,
            'tutor_id': tutor.id,
            'nombre': tutor.nombre_completo(),
            'huella_registrada': tutor.huella_registrada,
            'tiene_imagen': bool(tutor.huella_imagen),
            'imagen_url': tutor.huella_imagen.url if tutor.huella_imagen else None,
            'tiene_template': bool(tutor.huella_template),
            'template_size': len(tutor.huella_template) if tutor.huella_template else 0,
            'fecha_registro': tutor.fecha_registro_huella.isoformat() if tutor.fecha_registro_huella else None
        })
    except Tutor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Tutor no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def buscar_tutores_ajax(request):
    """Búsqueda de tutores vía AJAX"""
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'tutores': []})

    tutores = (
        Tutor.objects
        .filter(activo=True)
        .filter(
            Q(nombre__icontains=query) |
            Q(apellido_paterno__icontains=query) |
            Q(apellido_materno__icontains=query) |
            Q(numero_identificacion__icontains=query) |
            Q(telefono__icontains=query)
        )
        [:26]
    )

    tutores_data = [
        {
            'id': tutor.id,
            'nombre_completo': tutor.nombre_completo,
            'telefono': tutor.telefono,
            'parentesco': tutor.get_parentesco_display(),
            'huella_registrada': tutor.huella_registrada,
            'numero_identificacion': tutor.numero_identificacion,
        }
        for tutor in tutores
    ]

    return JsonResponse({'tutores': tutores_data})

# VISTAS ACTUALIZADAS - Usando FeatureSet para verificación

@csrf_exempt
def verificar_huella_inicio(request):
    """Iniciar verificación de huella"""
    if request.method == 'POST':
        try:
            # Iniciar captura en el servidor .NET
            response = requests.get(
                'http://localhost:5000/capturar?persona_id=verificacion',
                timeout=2
            )
            
            if response.status_code == 200:
                return JsonResponse({
                    'success': True,
                    'mensaje': 'Coloque su dedo en el lector'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'mensaje': 'Error al iniciar captura'
                })
        except requests.exceptions.ConnectionError:
            return JsonResponse({
                'success': False,
                'mensaje': 'Lector no disponible. Verifique que el servidor .NET esté ejecutándose.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'mensaje': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False}, status=405)


@csrf_exempt
def verificar_huella_estado(request):
    """Verificar estado y comparar usando FeatureSet"""
    if request.method == 'GET':
        try:
            # Consultar estado de captura
            response = requests.get('http://localhost:5000/estado', timeout=2)
            estado = response.json()
            
            # Si aún no se completa
            if not estado.get('completado'):
                return JsonResponse({
                    'completado': False,
                    'mensaje': 'Esperando huella...'
                })
            
            # *** USAR FEATURESET EN LUGAR DE TEMPLATE ***
            featureset_capturado = estado.get('huella_featureset')
            
            if not featureset_capturado:
                return JsonResponse({
                    'completado': True,
                    'success': False,
                    'mensaje': 'No se capturó FeatureSet'
                })
            
            print(f"\n{'='*60}")
            print(f"🔍 VERIFICACIÓN DE HUELLA (FeatureSet)")
            print(f"{'='*60}")
            print(f"FeatureSet capturado: {len(featureset_capturado)} chars")
            
            # Obtener tutores con huellas registradas
            tutores = Tutor.objects.filter(
                huella_registrada=True,
                huella_template__isnull=False,
                activo=True
            )
            
            print(f"Tutores a comparar: {tutores.count()}")
            
            if tutores.count() == 0:
                return JsonResponse({
                    'completado': True,
                    'success': False,
                    'mensaje': 'No hay tutores con huellas registradas'
                })
            
            # Preparar datos: FeatureSet + Templates de tutores
            tutores_data = []
            for tutor in tutores:
                try:
                    template_base64 = base64.b64encode(tutor.huella_template).decode('utf-8')
                    tutores_data.append({
                        'id': tutor.id,
                        'template': template_base64
                    })
                    print(f"  - Tutor {tutor.id}: {tutor.nombre_completo()}")
                except Exception as e:
                    print(f"  ✗ Error con tutor {tutor.id}: {e}")
            
            # Enviar a verificar: FeatureSet capturado vs Templates guardados
            print(f"\n📤 Enviando a servidor .NET...")
            
            response_verificacion = requests.post(
                'http://localhost:5000/verificar',
                json={
                    'feature_set_capturado': featureset_capturado,  # FeatureSet actual
                    'tutores': tutores_data  # Templates guardados
                },
                timeout=10
            )
            
            resultado = response_verificacion.json()
            print(f"📥 Respuesta: {resultado}")
            
            if resultado.get('success'):
                tutor_id = resultado.get('tutor_id')
                far_achieved = resultado.get('far_achieved', 'N/A')
                
                tutor = Tutor.objects.get(id=tutor_id)
                ninos = tutor.ninos.filter(activo=True)
                
                print(f"")
                print(f"{'='*60}")
                print(f"✅ TUTOR IDENTIFICADO")
                print(f"{'='*60}")
                print(f"ID: {tutor.id}")
                print(f"Nombre: {tutor.nombre_completo()}")
                print(f"FAR Achieved: {far_achieved}")
                print(f"Niños autorizados: {ninos.count()}")
                print(f"{'='*60}\n")
                
                # ⭐ CORRECCIÓN: Convertir objeto Grupo a string ⭐
                ninos_data = []
                for n in ninos:
                    ninos_data.append({
                        'id': n.id,
                        'nombre': n.nombre_completo(),
                        'grupo': str(n.grupo) if n.grupo else 'Sin grupo',  # ← AQUÍ ESTÁ LA CORRECCIÓN
                        'edad': n.edad(),
                        'foto_url': n.foto.url if n.foto else None
                    })
                
                return JsonResponse({
                    'completado': True,
                    'success': True,
                    'tutor': {
                        'id': tutor.id,
                        'nombre': tutor.nombre_completo(),
                        'parentesco': tutor.get_parentesco_display(),
                        'telefono': tutor.telefono,
                        'foto_url': tutor.huella_imagen.url if tutor.huella_imagen else None
                    },
                    'ninos': ninos_data,
                    'far_achieved': far_achieved
                })
            else:
                print(f"❌ No se encontró coincidencia")
                return JsonResponse({
                    'completado': True,
                    'success': False,
                    'mensaje': 'Huella no reconocida'
                })
                
        except requests.exceptions.ConnectionError:
            return JsonResponse({
                'completado': False,
                'error': 'No se puede conectar con el servidor .NET'
            })
        except Exception as e:
            print(f"❌ Error en verificación: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'completado': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False}, status=405)



# ============================================
# VISTAS DE COLONIAS (CÓDIGO POSTAL)
# ============================================

def buscar_colonias_cp(request):
    """Busca colonias por código postal o por nombre desde la base de datos"""
    cp = request.GET.get('cp', '').strip()
    q  = request.GET.get('q', '').strip()

    def serializar(col):
        """Convierte un objeto o dict de Colonia al formato que espera el JS"""
        if isinstance(col, dict):
            return {
                "id":       col['id'],
                "nombre":   col['d_asenta'],
                "municipio": col['D_mnpio'],
                "estado":   col['d_estado'],
                "ciudad":   col['D_mnpio'],   # se usaba d_ciudad; ahora usamos municipio
                "cp":       col['d_codigo'],
                # tipo_asentamiento ya no existe, el JS no lo requiere
            }
        return {
            "id":       col.id,
            "nombre":   col.d_asenta,
            "municipio": col.D_mnpio,
            "estado":   col.d_estado,
            "ciudad":   col.D_mnpio,
            "cp":       col.d_codigo,
        }

    # ── Búsqueda por CP ──
    if cp:
        if not cp.isdigit() or len(cp) != 5:
            return JsonResponse({"success": False, "error": "Código postal inválido"})

        try:
            colonias = Colonia.objects.filter(d_codigo=cp).order_by('d_asenta')
            if not colonias.exists():
                return JsonResponse({"success": False,
                                     "error": f"No se encontraron colonias para el CP {cp}"})

            return JsonResponse({
                "success": True,
                "fuente":  "base_de_datos",
                "colonias": [serializar(c) for c in colonias],
                "total":    colonias.count()
            })

        except Exception as e:
            import traceback
            return JsonResponse({"success": False, "error": str(e),
                                 "traceback": traceback.format_exc()})

    # ── Búsqueda por texto libre ──
    elif q and len(q) >= 3:
        try:
            from django.db.models import Q
            colonias = (
                Colonia.objects
                .filter(Q(d_asenta__icontains=q) | Q(D_mnpio__icontains=q))
                .values('id', 'd_asenta', 'D_mnpio', 'd_estado', 'd_codigo')
                .order_by('d_asenta')[:40]
            )
            return JsonResponse({
                "success": True,
                "fuente":  "base_de_datos",
                "colonias": [serializar(c) for c in colonias],
                "total":    len(list(colonias))
            })

        except Exception as e:
            import traceback
            return JsonResponse({"success": False, "error": str(e),
                                 "traceback": traceback.format_exc()})

    return JsonResponse({"success": False,
                         "error": "Proporciona cp o q (mínimo 3 caracteres)"})

# ============================================
# VISTAS DE DEPENDENCIAS Y DEPARTAMENTOS
# ============================================

@login_required
@admin_requerido
def lista_dependencias(request):
    """Lista de dependencias activas e inactivas"""
    dependencias_activas = Dependencia.objects.filter(activo=True).order_by('nombre')
    dependencias_inactivas = Dependencia.objects.filter(activo=False).order_by('nombre')
    
    return render(request, 'guarderia/dependencias/lista.html', {
        'dependencias_activas': dependencias_activas,
        'dependencias_inactivas': dependencias_inactivas
    })


@login_required
@admin_requerido
def registrar_dependencia(request):
    """Registrar nueva dependencia"""
    if request.method == 'POST':
        form = DependenciaForm(request.POST)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            dependencia = form.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'Dependencia {dependencia.nombre} registrada',
                    'dependencia_id': dependencia.id
                })
            else:
                messages.success(request, f'Dependencia {dependencia.nombre} registrada')
                return redirect('guarderia:lista_dependencias')
        else:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    else:
        form = DependenciaForm()
    
    return render(request, 'guarderia/dependencias/registrar.html', {'form': form})

@login_required
@admin_requerido
def editar_dependencia(request, dependencia_id):
    """Editar dependencia"""
    dependencia = get_object_or_404(Dependencia, id=dependencia_id)
    
    if request.method == 'POST':
        form = DependenciaForm(request.POST, instance=dependencia)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Dependencia {dependencia.nombre} actualizada')
            return redirect('guarderia:lista_dependencias')
    else:
        form = DependenciaForm(instance=dependencia)
    
    return render(request, 'guarderia/dependencias/editar.html', {
        'form': form,
        'dependencia': dependencia
    })


@login_required
@admin_requerido
def lista_departamentos(request):
    """Lista de departamentos activos e inactivos"""
    departamentos_activos = Departamento.objects.filter(activo=True).select_related('dependencia').order_by('dependencia__nombre', 'nombre')
    departamentos_inactivos = Departamento.objects.filter(activo=False).select_related('dependencia').order_by('dependencia__nombre', 'nombre')
    
    return render(request, 'guarderia/departamentos/lista.html', {
        'departamentos_activos': departamentos_activos,
        'departamentos_inactivos': departamentos_inactivos
    })


@login_required
@admin_requerido
def editar_departamento(request, departamento_id):
    """Editar departamento"""
    departamento = get_object_or_404(Departamento, id=departamento_id)
    
    if request.method == 'POST':
        form = DepartamentoForm(request.POST, instance=departamento)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Departamento {departamento.nombre} actualizado')
            return redirect('guarderia:lista_departamentos')
    else:
        form = DepartamentoForm(instance=departamento)
    
    return render(request, 'guarderia/departamentos/editar.html', {
        'form': form,
        'departamento': departamento
    })



@login_required
@admin_requerido
@require_http_methods(["GET"])
def obtener_departamentos_ajax(request):
    """Obtener departamentos de una dependencia vía AJAX"""
    dependencia_id = request.GET.get('dependencia_id')
    
    if not dependencia_id:
        return JsonResponse({'departamentos': []})
    
    try:
        departamentos = Departamento.objects.filter(
            dependencia_id=dependencia_id,
            activo=True
        ).values('id', 'nombre')
        
        return JsonResponse({
            'success': True,
            'departamentos': list(departamentos)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@admin_requerido
def registrar_departamento(request):
    """Registrar nuevo departamento"""
    if request.method == 'POST':
        form = DepartamentoForm(request.POST)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            departamento = form.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'Departamento {departamento.nombre} registrado',
                    'departamento_id': departamento.id
                })
            else:
                messages.success(request, f'Departamento {departamento.nombre} registrado')
                return redirect('guarderia:lista_dependencias')
        else:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    else:
        form = DepartamentoForm()
    
    return render(request, 'guarderia/departamentos/registrar.html', {'form': form})

@login_required
@admin_requerido
def lista_servicios_medicos(request):
    """Lista de servicios médicos"""
    servicios_activos   = ServicioMedico.objects.filter(activo=True).order_by('nombre')
    servicios_inactivos = ServicioMedico.objects.filter(activo=False).order_by('nombre')
    return render(request, 'guarderia/servicios_medicos/lista.html', {
        'servicios_activos':   servicios_activos,
        'servicios_inactivos': servicios_inactivos,
    })


@login_required
@admin_requerido
def registrar_servicio_medico(request):
    """Registrar nuevo servicio médico"""
    if request.method == 'POST':
        form = ServicioMedicoForm(request.POST)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            servicio = form.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'Servicio médico {servicio.nombre} registrado',
                    'servicio_id': servicio.id
                })
            else:
                messages.success(request, f'Servicio médico {servicio.nombre} registrado')
                return redirect('guarderia:lista_servicios_medicos')
        else:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    else:
        form = ServicioMedicoForm()
    
    return render(request, 'guarderia/servicios_medicos/registrar.html', {'form': form})


@login_required
@admin_requerido
def editar_servicio_medico(request, servicio_id):
    """Editar servicio médico"""
    servicio = get_object_or_404(ServicioMedico, id=servicio_id)
    
    if request.method == 'POST':
        form = ServicioMedicoForm(request.POST, instance=servicio)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Servicio médico {servicio.nombre} actualizado')
            return redirect('guarderia:lista_servicios_medicos')
    else:
        form = ServicioMedicoForm(instance=servicio)
    
    return render(request, 'guarderia/servicios_medicos/editar.html', {
        'form': form,
        'servicio': servicio
    })


# ========== GRUPOS ==========

@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
def lista_grupos(request):
    """Lista de grupos con estadísticas"""
    def enriquecer(qs):
        resultado = []
        for grupo in qs:
            resultado.append({
                'grupo':                grupo,
                'ninos_asignados':      grupo.ninos_asignados(),
                'capacidad_disponible': grupo.capacidad_disponible(),
                'porcentaje_ocupacion': grupo.porcentaje_ocupacion(),
                'esta_lleno':           grupo.esta_lleno(),
            })
        return resultado

    grupos_activos   = enriquecer(Grupo.objects.filter(activo=True).order_by('tipo', 'grado', 'nombre'))
    grupos_inactivos = enriquecer(Grupo.objects.filter(activo=False).order_by('tipo', 'grado', 'nombre'))

    return render(request, 'guarderia/grupos/lista.html', {
        'grupos_activos':   grupos_activos,
        'grupos_inactivos': grupos_inactivos,
    })


@login_required
@admin_requerido
def registrar_grupo(request):
    """Registrar nuevo grupo"""
    if request.method == 'POST':
        form = GrupoForm(request.POST)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            grupo = form.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'Grupo {grupo.nombre} registrado',
                    'grupo_id': grupo.id
                })
            else:
                messages.success(request, f'Grupo {grupo.nombre} registrado exitosamente')
                return redirect('guarderia:lista_grupos')
        else:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    else:
        form = GrupoForm()
    
    return render(request, 'guarderia/grupos/registrar.html', {'form': form})


@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
def detalle_grupo(request, grupo_id):
    """Ver detalles de un grupo con lista de asistencia del día actual"""
    from django.utils import timezone
    from django.db.models import Subquery, OuterRef

    grupo  = get_object_or_404(Grupo, id=grupo_id)
    hoy    = timezone.localdate()
    ninos  = grupo.ninos.filter(activo=True).order_by('apellido_paterno', 'nombre')

    # IDs de niños que tienen al menos una ENTRADA hoy
    ninos_con_entrada_hoy = (
        RegistroAcceso.objects
        .filter(
            nino__grupo=grupo,
            tipo='ENTRADA',
            fecha_hora__date=hoy,
            verificacion_exitosa=True,
        )
        .values_list('nino_id', flat=True)
        .distinct()
    )

    # Para cada niño con entrada, traer el último registro de hoy
    # (puede ser ENTRADA o SALIDA — para saber si sigue dentro)
    from django.db.models import Max

    # Último registro de hoy por niño
    ultimo_registro_id = (
        RegistroAcceso.objects
        .filter(nino=OuterRef('nino'), fecha_hora__date=hoy)
        .order_by('-fecha_hora')
        .values('id')[:1]
    )

    registros_hoy = (
        RegistroAcceso.objects
        .filter(
            nino_id__in=ninos_con_entrada_hoy,
            id__in=Subquery(
                RegistroAcceso.objects
                .filter(nino=OuterRef('nino'), fecha_hora__date=hoy)
                .order_by('-fecha_hora')
                .values('id')[:1]
            )
        )
        .select_related('nino', 'tutor')
        .order_by('nino__apellido_paterno', 'nino__nombre')
    )

    # Hora de primera entrada de cada niño hoy
    primera_entrada = {}
    for reg in RegistroAcceso.objects.filter(
        nino_id__in=ninos_con_entrada_hoy,
        tipo='ENTRADA',
        fecha_hora__date=hoy,
    ).order_by('fecha_hora'):
        if reg.nino_id not in primera_entrada:
            primera_entrada[reg.nino_id] = reg.fecha_hora

    # Armar lista de asistencia
    asistencia = []
    for reg in registros_hoy:
        asistencia.append({
            'nino':           reg.nino,
            'tutor':          reg.tutor,
            'hora_entrada':   primera_entrada.get(reg.nino_id),
            'ultimo_estado':  reg.tipo,       # ENTRADA o SALIDA
            'sigue_dentro':   reg.tipo == 'ENTRADA',
        })

    return render(request, 'guarderia/grupos/detalle.html', {
        'grupo':                grupo,
        'ninos':                ninos,
        'ninos_asignados':      grupo.ninos_asignados(),
        'capacidad_disponible': grupo.capacidad_disponible(),
        'porcentaje_ocupacion': grupo.porcentaje_ocupacion(),
        'esta_lleno':           grupo.esta_lleno(),
        'asistencia':           asistencia,
        'hoy':                  hoy,
        'total_presentes':      sum(1 for a in asistencia if a['sigue_dentro']),
        'total_asistencia':     len(asistencia),
    })


@login_required
@admin_requerido
def editar_grupo(request, grupo_id):
    """Editar grupo"""
    grupo = get_object_or_404(Grupo, id=grupo_id)
    
    if request.method == 'POST':
        form = GrupoForm(request.POST, instance=grupo)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Grupo {grupo.nombre} actualizado')
            return redirect('guarderia:detalle_grupo', grupo_id=grupo.id)
    else:
        form = GrupoForm(instance=grupo)
    
    return render(request, 'guarderia/grupos/editar.html', {
        'form': form,
        'grupo': grupo
    })


@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
@require_http_methods(["GET"])
def obtener_grupos_disponibles_ajax(request):
    """Obtener grupos con disponibilidad vía AJAX"""
    tipo = request.GET.get('tipo')  # Filtrar por tipo si se proporciona
    
    grupos = Grupo.objects.filter(activo=True)
    
    if tipo:
        grupos = grupos.filter(tipo=tipo)
    
    grupos_data = []
    for grupo in grupos:
        ninos_count = grupo.ninos_asignados()
        disponible = ninos_count < grupo.capacidad_maxima
        
        grupos_data.append({
            'id': grupo.id,
            'nombre': str(grupo),
            'tipo': grupo.get_tipo_display(),
            'grado': grupo.grado,
            'capacidad_maxima': grupo.capacidad_maxima,
            'ninos_asignados': ninos_count,
            'disponible': disponible,
            'porcentaje_ocupacion': grupo.porcentaje_ocupacion()
        })
    
    return JsonResponse({
        'success': True,
        'grupos': grupos_data
    })


# ========== OBSERVACIONES DE NIÑOS ==========

@login_required
def lista_observaciones(request):
    """Lista de todas las observaciones"""
    # Filtros
    nino_id = request.GET.get('nino')
    tipo = request.GET.get('tipo')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    importantes = request.GET.get('importantes')
    
    observaciones = ObservacionNino.objects.select_related('nino', 'registrado_por')
    
    if nino_id:
        observaciones = observaciones.filter(nino_id=nino_id)
    if tipo:
        observaciones = observaciones.filter(tipo=tipo)
    if fecha_desde:
        observaciones = observaciones.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        observaciones = observaciones.filter(fecha__lte=fecha_hasta)
    if importantes:
        observaciones = observaciones.filter(importante=True)
    
    observaciones = observaciones.order_by('-fecha', '-hora')[:100]
    
    # Para el filtro
    ninos = Nino.objects.filter(activo=True).order_by('apellido_paterno', 'nombre')
    
    return render(request, 'guarderia/observaciones/lista.html', {
        'observaciones': observaciones,
        'ninos': ninos,
        'tipo_choices': ObservacionNino.TIPO_OBSERVACION_CHOICES
    })


@login_required
def registrar_observacion(request):
    """Registrar nueva observación"""
    if request.method == 'POST':
        form = ObservacionNinoForm(request.POST)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            observacion = form.save(commit=False)
            observacion.registrado_por = request.user
            observacion.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'Observación registrada para {observacion.nino.nombre_completo()}',
                    'observacion_id': observacion.id
                })
            else:
                messages.success(request, f'Observación registrada para {observacion.nino.nombre_completo()}')
                return redirect('guarderia:lista_observaciones')
        else:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    else:
        # Si viene nino_id en GET, pre-seleccionar el niño
        nino_id = request.GET.get('nino_id')
        initial = {}
        if nino_id:
            initial['nino'] = nino_id
        
        form = ObservacionNinoForm(initial=initial)
    
    return render(request, 'guarderia/observaciones/registrar.html', {'form': form})


@login_required
def observaciones_nino(request, nino_id):
    """Ver todas las observaciones de un niño específico"""
    nino = get_object_or_404(Nino, id=nino_id)
    observaciones = nino.observaciones.select_related('registrado_por').order_by('-fecha', '-hora')
    
    # Estadísticas
    total = observaciones.count()
    importantes = observaciones.filter(importante=True).count()
    pendientes_notificar = observaciones.filter(notificar_tutor=True, notificado=False).count()
    
    return render(request, 'guarderia/observaciones/por_nino.html', {
        'nino': nino,
        'observaciones': observaciones,
        'total': total,
        'importantes': importantes,
        'pendientes_notificar': pendientes_notificar
    })


@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
def editar_observacion(request, observacion_id):
    """Editar una observación"""
    observacion = get_object_or_404(ObservacionNino, id=observacion_id)
    
    if request.method == 'POST':
        form = ObservacionNinoForm(request.POST, instance=observacion)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Observación actualizada')
            return redirect('guarderia:observaciones_nino', nino_id=observacion.nino.id)
    else:
        form = ObservacionNinoForm(instance=observacion)
    
    return render(request, 'guarderia/observaciones/editar.html', {
        'form': form,
        'observacion': observacion
    })


@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
@require_http_methods(["POST"])
def marcar_observacion_notificada(request, observacion_id):
    """Marcar una observación como notificada"""
    observacion = get_object_or_404(ObservacionNino, id=observacion_id)
    
    observacion.notificado = True
    observacion.fecha_notificacion = timezone.now()
    observacion.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Observación marcada como notificada'
    })
    
@login_required
def dashboard(request):
    """Dashboard principal con estadísticas de la guardería"""
    
    # ========== ESTADÍSTICAS GENERALES ==========
    total_ninos = Nino.objects.filter(activo=True).count()
    total_tutores = Tutor.objects.filter(activo=True).count()
    total_grupos = Grupo.objects.filter(activo=True).count()
    
    # Tutores con huella registrada
    tutores_con_huella = Tutor.objects.filter(
        activo=True, 
        huella_registrada=True
    ).count()
    porcentaje_huellas = round((tutores_con_huella / total_tutores * 100), 1) if total_tutores > 0 else 0
    
    # ========== NIÑOS POR GRUPO ==========
    ninos_por_grupo = Grupo.objects.filter(activo=True).annotate(
        total_ninos=Count('ninos', filter=Q(ninos__activo=True))
    ).values('nombre', 'tipo', 'capacidad_maxima', 'total_ninos')
    
    # Calcular ocupación de grupos
    grupos_stats = []
    for grupo in ninos_por_grupo:
        porcentaje = round((grupo['total_ninos'] / grupo['capacidad_maxima'] * 100), 1) if grupo['capacidad_maxima'] > 0 else 0
        grupos_stats.append({
            'nombre': grupo['nombre'],
            'tipo': grupo['tipo'],
            'total': grupo['total_ninos'],
            'capacidad': grupo['capacidad_maxima'],
            'porcentaje': porcentaje
        })
    
    # ========== REGISTROS DE HOY ==========
    hoy = datetime.now().date()
    registros_hoy = RegistroAcceso.objects.filter(
        fecha_hora__date=hoy
    ).select_related('nino', 'tutor')
    
    entradas_hoy = registros_hoy.filter(tipo='ENTRADA').count()
    salidas_hoy = registros_hoy.filter(tipo='SALIDA').count()
    ninos_presentes = entradas_hoy - salidas_hoy
    
    # ========== ÚLTIMOS REGISTROS ==========
    ultimos_registros = RegistroAcceso.objects.select_related(
        'nino', 'tutor'
    ).order_by('-fecha_hora')[:10]
    
    # ========== OBSERVACIONES RECIENTES ==========
    observaciones_recientes = ObservacionNino.objects.select_related(
        'nino', 'registrado_por'
    ).order_by('-fecha', '-hora')[:5]
    
    # Observaciones importantes sin notificar
    observaciones_pendientes = ObservacionNino.objects.filter(
        importante=True,
        notificar_tutor=True,
        notificado=False
    ).count()
    
    # ========== REGISTROS DE LA SEMANA ==========
    hace_7_dias = hoy - timedelta(days=7)
    registros_semana = []
    
    for i in range(7):
        fecha = hoy - timedelta(days=6-i)
        entradas = RegistroAcceso.objects.filter(
            fecha_hora__date=fecha,
            tipo='ENTRADA'
        ).count()
        salidas = RegistroAcceso.objects.filter(
            fecha_hora__date=fecha,
            tipo='SALIDA'
        ).count()
        
        registros_semana.append({
            'fecha': fecha.strftime('%d/%m'),
            'entradas': entradas,
            'salidas': salidas
        })
    
    # ========== TUTORES POR DEPENDENCIA ==========
    tutores_por_dependencia = Dependencia.objects.filter(
        activo=True
    ).annotate(
        total_tutores=Count('trabajadores', filter=Q(trabajadores__activo=True))
    ).order_by('-total_tutores')[:5]
    
    # ========== NIÑOS POR EDAD ==========
    ninos_activos = Nino.objects.filter(activo=True)
    
    lactantes = 0  # 0-1 año
    maternales = 0  # 1-3 años
    preescolares = 0  # 3-6 años
    
    for nino in ninos_activos:
        edad = nino.edad()
        if edad < 1:
            lactantes += 1
        elif edad < 3:
            maternales += 1
        else:
            preescolares += 1
    
    # ========== ALERTAS Y NOTIFICACIONES ==========
    tutores_sin_huella = Tutor.objects.filter(
        activo=True,
        huella_registrada=False
    ).count()
    
    ninos_sin_grupo = Nino.objects.filter(
        activo=True,
        grupo__isnull=True
    ).count()
    
    context = {
        # Estadísticas generales
        'total_ninos': total_ninos,
        'total_tutores': total_tutores,
        'total_grupos': total_grupos,
        'tutores_con_huella': tutores_con_huella,
        'porcentaje_huellas': porcentaje_huellas,
        
        # Registros de hoy
        'entradas_hoy': entradas_hoy,
        'salidas_hoy': salidas_hoy,
        'ninos_presentes': ninos_presentes,
        
        # Grupos
        'grupos_stats': grupos_stats,
        
        # Registros recientes
        'ultimos_registros': ultimos_registros,
        
        # Observaciones
        'observaciones_recientes': observaciones_recientes,
        'observaciones_pendientes': observaciones_pendientes,
        
        # Gráficas
        'registros_semana': registros_semana,
        'tutores_por_dependencia': tutores_por_dependencia,
        
        # Distribución por edad
        'lactantes': lactantes,
        'maternales': maternales,
        'preescolares': preescolares,
        
        # Alertas
        'tutores_sin_huella': tutores_sin_huella,
        'ninos_sin_grupo': ninos_sin_grupo,
    }
    
    return render(request, 'guarderia/dashboard.html', context)

# ============================================
# FUNCIONES DE PAPELERA - Agregar a views.py
# ============================================

@login_required
@admin_requerido
@require_http_methods(["POST"])
def enviar_departamento_papelera(request, departamento_id):
    """Enviar departamento a papelera (marcar como inactivo)"""
    try:
        departamento = get_object_or_404(Departamento, id=departamento_id)
        departamento.activo = False
        departamento.save()
        
        messages.success(request, f'Departamento {departamento.nombre} enviado a papelera')
        
        return JsonResponse({
            'success': True,
            'message': f'Departamento {departamento.nombre} enviado a papelera'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@admin_requerido
@require_http_methods(["POST"])
def restaurar_departamento(request, departamento_id):
    """Restaurar departamento desde papelera (marcar como activo)"""
    try:
        departamento = get_object_or_404(Departamento, id=departamento_id)
        departamento.activo = True
        departamento.save()
        
        messages.success(request, f'Departamento {departamento.nombre} restaurado exitosamente')
        
        return JsonResponse({
            'success': True,
            'message': f'Departamento {departamento.nombre} restaurado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@admin_requerido
@require_http_methods(["POST"])
def enviar_dependencia_papelera(request, dependencia_id):
    """Enviar dependencia a papelera (marcar como inactivo)"""
    try:
        dependencia = get_object_or_404(Dependencia, id=dependencia_id)
        dependencia.activo = False
        dependencia.save()
        
        messages.success(request, f'Dependencia {dependencia.nombre} enviada a papelera')
        
        return JsonResponse({
            'success': True,
            'message': f'Dependencia {dependencia.nombre} enviada a papelera'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@login_required
@admin_requerido
@require_http_methods(["POST"])
def restaurar_dependencia(request, dependencia_id):
    """Restaurar dependencia desde papelera (marcar como activo)"""
    try:
        dependencia = get_object_or_404(Dependencia, id=dependencia_id)
        dependencia.activo = True
        dependencia.save()
        
        messages.success(request, f'Dependencia {dependencia.nombre} restaurada exitosamente')
        
        return JsonResponse({
            'success': True,
            'message': f'Dependencia {dependencia.nombre} restaurada'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


# ── Servicios Médicos ──────────────────────

@login_required
@admin_requerido
@require_http_methods(["POST"])
def enviar_servicio_papelera(request, servicio_id):
    try:
        servicio = get_object_or_404(ServicioMedico, id=servicio_id)
        servicio.activo = False
        servicio.save()
        return JsonResponse({'success': True, 'message': f'Servicio {servicio.nombre} enviado a papelera'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@admin_requerido
@require_http_methods(["POST"])
def restaurar_servicio(request, servicio_id):
    try:
        servicio = get_object_or_404(ServicioMedico, id=servicio_id)
        servicio.activo = True
        servicio.save()
        return JsonResponse({'success': True, 'message': f'Servicio {servicio.nombre} restaurado'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ── Grupos ─────────────────────────────────

@login_required
@admin_requerido
@require_http_methods(["POST"])
def enviar_grupo_papelera(request, grupo_id):
    try:
        grupo = get_object_or_404(Grupo, id=grupo_id)
        grupo.activo = False
        grupo.save()
        return JsonResponse({'success': True, 'message': f'Grupo {grupo.nombre} enviado a papelera'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@admin_requerido
@require_http_methods(["POST"])
def restaurar_grupo(request, grupo_id):
    try:
        grupo = get_object_or_404(Grupo, id=grupo_id)
        grupo.activo = True
        grupo.save()
        return JsonResponse({'success': True, 'message': f'Grupo {grupo.nombre} restaurado'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ── Tutores ────────────────────────────────

@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
@require_http_methods(["POST"])
def enviar_tutor_papelera(request, tutor_id):
    try:
        tutor = get_object_or_404(Tutor, id=tutor_id)
        tutor.activo = False
        tutor.save()
        return JsonResponse({'success': True, 'message': f'Tutor {tutor.nombre_completo()} enviado a papelera'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
@require_http_methods(["POST"])
def restaurar_tutor(request, tutor_id):
    try:
        tutor = get_object_or_404(Tutor, id=tutor_id)
        tutor.activo = True
        tutor.save()
        return JsonResponse({'success': True, 'message': f'Tutor {tutor.nombre_completo()} restaurado'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ── Niños ──────────────────────────────────

@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
@require_http_methods(["POST"])
def enviar_nino_papelera(request, nino_id):
    try:
        nino = get_object_or_404(Nino, id=nino_id)
        nino.activo = False
        nino.save()
        return JsonResponse({'success': True, 'message': f'{nino.nombre_completo()} enviado a papelera'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
@require_http_methods(["POST"])
def restaurar_nino(request, nino_id):
    try:
        nino = get_object_or_404(Nino, id=nino_id)
        nino.activo = True
        nino.save()
        return JsonResponse({'success': True, 'message': f'{nino.nombre_completo()} restaurado'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

  # ============================================================
# REEMPLAZA la función finalizar_ciclo_escolar en views.py
# ============================================================

@login_required
@admin_requerido
def finalizar_ciclo_escolar(request):
    """
    Finalizar ciclo escolar - Promoción masiva con propuesta automática
    El sistema sugiere el siguiente grupo lógico, el admin puede editarlo.
    """

    # Orden de tipos y grados para calcular propuesta automática
    ORDEN_TIPOS  = ['LACTANTE', 'MATERNAL', 'PREESCOLAR']
    ORDEN_GRADOS = ['1er año', '2do año', '3er año']

    def siguiente_grupo(grupo_actual, todos_los_grupos):
        """
        Dado un grupo, devuelve el grupo destino sugerido.
        Busca el siguiente en la secuencia tipo+grado.
        Si es el último, retorna None (graduar).
        """
        try:
            idx_tipo  = ORDEN_TIPOS.index(grupo_actual.tipo)
            idx_grado = ORDEN_GRADOS.index(grupo_actual.grado)
        except ValueError:
            return None

        # Intentar siguiente grado dentro del mismo tipo
        for g in ORDEN_GRADOS[idx_grado + 1:]:
            candidatos = [gr for gr in todos_los_grupos
                          if gr.tipo == grupo_actual.tipo and gr.grado == g and gr.id != grupo_actual.id]
            if candidatos:
                return candidatos[0]

        # Intentar primer grado del siguiente tipo
        for t in ORDEN_TIPOS[idx_tipo + 1:]:
            candidatos = [gr for gr in todos_los_grupos
                          if gr.tipo == t and gr.id != grupo_actual.id]
            if candidatos:
                # El de menor grado dentro de ese tipo
                candidatos_ordenados = sorted(
                    candidatos,
                    key=lambda x: ORDEN_GRADOS.index(x.grado) if x.grado in ORDEN_GRADOS else 99
                )
                return candidatos_ordenados[0]

        # No hay siguiente → graduar
        return None

    # ── POST: ejecutar promociones ──────────────────────────────────────
    if request.method == 'POST':
        try:
            data       = json.loads(request.body)
            promociones = data.get('promociones', {})

            with transaction.atomic():
                resultado = {'promovidos': [], 'graduados': [], 'errores': []}

                for grupo_origen_id, grupo_destino_id in promociones.items():
                    grupo_origen = Grupo.objects.get(id=grupo_origen_id)
                    ninos        = Nino.objects.filter(grupo=grupo_origen, activo=True)

                    if grupo_destino_id == 'graduar':
                        for nino in ninos:
                            ObservacionNino.objects.create(
                                nino=nino,
                                tipo='ACADEMICO',
                                descripcion=f'Graduado del ciclo escolar {timezone.now().year}',
                                importante=True,
                                notificar_tutor=True,
                                registrado_por=request.user
                            )
                            nino.grupo = None
                            nino.activo = False 
                            nino.save()
                            resultado['graduados'].append({
                                'nino': nino.nombre_completo(),
                                'grupo_origen': str(grupo_origen)
                            })

                    elif grupo_destino_id:
                        grupo_destino = Grupo.objects.get(id=grupo_destino_id)
                        for nino in ninos:
                            nino.grupo = grupo_destino
                            nino.save()
                            resultado['promovidos'].append({
                                'nino': nino.nombre_completo(),
                                'de': str(grupo_origen),
                                'a': str(grupo_destino)
                            })

                return JsonResponse({
                    'success': True,
                    'mensaje': 'Ciclo escolar finalizado exitosamente',
                    'resultado': resultado,
                    'total_promovidos': len(resultado['promovidos']),
                    'total_graduados':  len(resultado['graduados'])
                })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'mensaje': str(e)}, status=500)

    # ── GET: mostrar vista con propuestas ───────────────────────────────
    todos_grupos = list(
        Grupo.objects.filter(activo=True).order_by('tipo', 'grado', 'nombre')
    )

    grupos_info = []
    for grupo in todos_grupos:
        sugerido = siguiente_grupo(grupo, todos_grupos)
        grupos_info.append({
            'grupo':        grupo,
            'ninos':        grupo.ninos.filter(activo=True),
            'total_ninos':  grupo.ninos.filter(activo=True).count(),
            'sugerido':     sugerido,       # objeto Grupo o None (=graduar)
        })

    grupos_destino = todos_grupos  # misma lista para los selects

    return render(request, 'guarderia/grupos/finalizar_ciclo.html', {
        'grupos_info':    grupos_info,
        'grupos_destino': grupos_destino,
    })
    
# ============================================================
# AGREGAR ESTAS DOS FUNCIONES AL FINAL DE guarderia/views.py
# ============================================================

@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
def reporte_tutores_dependencia(request):
    """
    Reporte: cuántos tutores hay por dependencia, quiénes son y cuáles son sus hijos.
    """
    filtro_dependencia = request.GET.get('dependencia', '')
    filtro_q           = request.GET.get('q', '').strip()

    # ── Queryset base de tutores activos ──────────────────────────────
    tutores_qs = Tutor.objects.filter(activo=True).select_related(
        'dependencia', 'departamento'
    ).prefetch_related('ninos')

    if filtro_dependencia:
        tutores_qs = tutores_qs.filter(dependencia_id=filtro_dependencia)

    if filtro_q:
        tutores_qs = tutores_qs.filter(
            Q(nombre__icontains=filtro_q) |
            Q(apellido_paterno__icontains=filtro_q) |
            Q(apellido_materno__icontains=filtro_q) |
            Q(numero_empleado__icontains=filtro_q)
        )

    # ── Agrupar por dependencia ───────────────────────────────────────
    from collections import defaultdict

    grupos_dep   = defaultdict(list)      # dependencia_pk  → [filas]
    sin_dep_list = []

    for tutor in tutores_qs:
        ninos_del_tutor = tutor.ninos.filter(activo=True)
        fila = {
            'tutor': tutor,
            'ninos': list(ninos_del_tutor),
        }
        if tutor.dependencia_id:
            grupos_dep[tutor.dependencia_id].append(fila)
        else:
            sin_dep_list.append(fila)

    # Construir lista ordenada
    dependencias_obj = {
        d.id: d
        for d in Dependencia.objects.filter(activo=True).order_by('nombre')
    }

    datos = []
    total_ninos_rel = set()

    for dep_id, filas in sorted(grupos_dep.items(),
                                 key=lambda x: dependencias_obj.get(x[0], type('', (), {'nombre': ''})()).nombre):
        dep_obj = dependencias_obj.get(dep_id)
        if dep_obj is None:
            try:
                dep_obj = Dependencia.objects.get(id=dep_id)
            except Dependencia.DoesNotExist:
                continue

        total_n = sum(len(f['ninos']) for f in filas)
        for f in filas:
            for n in f['ninos']:
                total_ninos_rel.add(n.id)

        datos.append({
            'dependencia': dep_obj,
            'tutores':     filas,
            'total_ninos': total_n,
        })

    # Niños de tutores sin dependencia
    for f in sin_dep_list:
        for n in f['ninos']:
            total_ninos_rel.add(n.id)

    # ── Estadísticas de cabecera ──────────────────────────────────────
    total_tutores_qs = Tutor.objects.filter(activo=True)
    total_dep_ids    = total_tutores_qs.exclude(
        dependencia__isnull=True
    ).values_list('dependencia_id', flat=True).distinct()

    context = {
        'datos':                   datos,
        'sin_dependencia':         sin_dep_list,
        'dependencias':            Dependencia.objects.filter(activo=True).order_by('nombre'),

        # Filtros activos
        'filtro_dependencia':      filtro_dependencia,
        'filtro_q':                filtro_q,

        # Estadísticas
        'total_dependencias':      total_dep_ids.count(),
        'total_tutores_con_dep':   total_tutores_qs.exclude(dependencia__isnull=True).count(),
        'tutores_sin_dep':         total_tutores_qs.filter(dependencia__isnull=True).count(),
        'total_ninos_relacionados': len(total_ninos_rel),
    }

    return render(request, 'guarderia/reportes/tutores_dependencia.html', context)


@login_required
@rol_requerido('ADMIN', 'EMPLEADO')
def reporte_asistencia_genero(request):
    """
    Reporte de asistencia filtrado por género (M / F / todos),
    con resumen por grupo y tabla detallada de registros.
    """
    from datetime import date as date_type

    filtro_genero     = request.GET.get('genero', '')
    filtro_grupo      = request.GET.get('grupo', '')
    filtro_fecha_desde = request.GET.get('fecha_desde', '')
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '')
    filtro_tipo       = request.GET.get('tipo', '')

    # ── Niños inscritos (para tabla inferior) ────────────────────────
    ninos_qs = Nino.objects.filter(activo=True).select_related('grupo').prefetch_related('tutores')

    if filtro_genero:
        ninos_qs = ninos_qs.filter(genero=filtro_genero)
    if filtro_grupo:
        ninos_qs = ninos_qs.filter(grupo_id=filtro_grupo)

    ninos_list = list(ninos_qs.order_by('grupo__tipo', 'grupo__grado', 'apellido_paterno', 'nombre'))

    # ── Estadísticas generales (sin filtro de género) ────────────────
    total_activos    = Nino.objects.filter(activo=True).count()
    total_masculino  = Nino.objects.filter(activo=True, genero='M').count()
    total_femenino   = Nino.objects.filter(activo=True, genero='F').count()
    pct_masculino    = round(total_masculino / total_activos * 100, 1) if total_activos else 0
    pct_femenino     = round(total_femenino  / total_activos * 100, 1) if total_activos else 0

    # ── Resumen por grupo ─────────────────────────────────────────────
    grupos_activos = Grupo.objects.filter(activo=True).order_by('tipo', 'grado', 'nombre')
    resumen_por_grupo = []

    for grupo in grupos_activos:
        base = Nino.objects.filter(activo=True, grupo=grupo)
        if filtro_genero:
            base = base.filter(genero=filtro_genero)
        masc = base.filter(genero='M').count()
        fem  = base.filter(genero='F').count()
        tot  = masc + fem
        if tot > 0 or not filtro_genero:
            resumen_por_grupo.append({
                'grupo':     str(grupo),
                'masculino': masc,
                'femenino':  fem,
                'total':     tot,
            })

    # Sin grupo
    base_sg = Nino.objects.filter(activo=True, grupo__isnull=True)
    if filtro_genero:
        base_sg = base_sg.filter(genero=filtro_genero)
    m_sg = base_sg.filter(genero='M').count()
    f_sg = base_sg.filter(genero='F').count()
    t_sg = m_sg + f_sg
    if t_sg > 0:
        resumen_por_grupo.append({
            'grupo':     'Sin grupo asignado',
            'masculino': m_sg,
            'femenino':  f_sg,
            'total':     t_sg,
        })

    # ── Registros de acceso (tabla superior derecha) ──────────────────
    registros_qs = RegistroAcceso.objects.select_related(
        'nino', 'tutor', 'nino__grupo'
    )

    if filtro_genero:
        registros_qs = registros_qs.filter(nino__genero=filtro_genero)
    if filtro_grupo:
        registros_qs = registros_qs.filter(nino__grupo_id=filtro_grupo)
    if filtro_tipo:
        registros_qs = registros_qs.filter(tipo=filtro_tipo)

    if filtro_fecha_desde:
        try:
            registros_qs = registros_qs.filter(
                fecha_hora__date__gte=datetime.strptime(filtro_fecha_desde, '%Y-%m-%d').date()
            )
        except ValueError:
            pass
    if filtro_fecha_hasta:
        try:
            registros_qs = registros_qs.filter(
                fecha_hora__date__lte=datetime.strptime(filtro_fecha_hasta, '%Y-%m-%d').date()
            )
        except ValueError:
            pass

    # Si no hay filtro de fechas se muestran los últimos 200 registros
    registros_list = list(registros_qs.order_by('-fecha_hora')[:200])

    context = {
        # Datos tablas
        'ninos':              ninos_list,
        'registros':          registros_list,
        'resumen_por_grupo':  resumen_por_grupo,
        'grupos':             grupos_activos,

        # Filtros activos
        'filtro_genero':      filtro_genero,
        'filtro_grupo':       filtro_grupo,
        'filtro_fecha_desde': filtro_fecha_desde,
        'filtro_fecha_hasta': filtro_fecha_hasta,
        'filtro_tipo':        filtro_tipo,

        # Estadísticas
        'total_ninos':           total_activos,
        'total_masculino':       total_masculino,
        'total_femenino':        total_femenino,
        'pct_masculino':         pct_masculino,
        'pct_femenino':          pct_femenino,
        'total_registros_periodo': len(registros_list),
    }

    return render(request, 'guarderia/reportes/asistencia_genero.html', context)

@login_required
@admin_requerido
def configuracion_guarderia(request):
    config = ConfiguracionGuarderia.get_solo()
    lista_minutos = [5,10,15,20,30,45,60,90,120]
    
    if request.method == 'POST':
        form = ConfiguracionGuarderiaForm(request.POST, instance=config)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            cfg = form.save(commit=False)
            cfg.actualizado_por = request.user
            cfg.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'Configuración guardada: {cfg.tiempo_minimo_entre_registros} minutos entre registros.',
                    'tiempo': cfg.tiempo_minimo_entre_registros,
                })
            messages.success(request, 'Configuración actualizada correctamente.')
            return redirect('guarderia:configuracion_guarderia')
        else:
            if is_ajax:
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            messages.error(request, 'Por favor corrige los errores.')
    else:
        form = ConfiguracionGuarderiaForm(instance=config)
    
    # Últimas 10 modificaciones de registros para mostrar contexto
    ultimos_registros = RegistroAcceso.objects.select_related(
        'nino', 'tutor'
    ).order_by('-fecha_hora')[:10]
    
    return render(request, 'guarderia/configuracion/tiempo_limite.html', {
        'form': form,
        'config': config,
        'ultimos_registros': ultimos_registros,
        "lista_minutos": lista_minutos
    })
# ============================================
# EMERGENCIA — Validar código de escalamiento
# ============================================

@csrf_exempt
@require_http_methods(["POST"])
def validar_codigo_escalamiento(request):
    from django.contrib.auth.hashers import check_password as django_check_password
    from login.models import Perfil

    try:
        data = json.loads(request.body)
        codigo_ingresado = str(data.get('codigo', '')).strip()

        # Buscar entre perfiles habilitados explícitamente + administradores (permiso implícito)
        from django.db.models import Q
        
        perfiles = Perfil.objects.filter(
            Q(puede_usar_codigo_escalamiento=True) | 
            Q(user__is_superuser=True) | 
            Q(rol__nombre__iexact='ADMIN')
        ).exclude(codigo_escalamiento__isnull=True).exclude(codigo_escalamiento='')

        perfil_valido = None
        for perfil in perfiles:
            if django_check_password(codigo_ingresado, perfil.codigo_escalamiento):
                perfil_valido = perfil
                break

        if not perfil_valido:
            return JsonResponse({
                'success': False,
                'mensaje': 'Código incorrecto. Inténtalo de nuevo.'
            })

        # Guardar en sesión quién validó
        request.session['emergencia_perfil_id'] = perfil_valido.id
        request.session['emergencia_usuario_nombre'] = perfil_valido.user.get_full_name()

        # Niños dentro...
        ninos_activos = Nino.objects.filter(activo=True)
        ninos_dentro = []
        for nino in ninos_activos:
            ultimo = RegistroAcceso.objects.filter(nino=nino).order_by('-fecha_hora').first()
            if ultimo and ultimo.tipo == 'ENTRADA':
                ninos_dentro.append({
                    'id': nino.id,
                    'nombre': nino.nombre_completo(),
                    'matricula': nino.numero_matricula or '—',
                    'grupo': str(nino.grupo) if nino.grupo else 'Sin grupo',
                    'foto_url': nino.foto.url if nino.foto else None,
                    'desde': ultimo.fecha_hora.strftime('%H:%M'),
                })

        return JsonResponse({
            'success': True,
            'ninos_dentro': ninos_dentro,
            'total': len(ninos_dentro),
        })

    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': f'Error: {str(e)}'}, status=500)


# ============================================
# EMERGENCIA — Registrar salida de emergencia
# ============================================

@csrf_exempt
@require_http_methods(["POST"])
def salida_emergencia(request):
    from login.models import Perfil

    try:
        perfil_id = request.session.get('emergencia_perfil_id')
        nombre_empleado = request.session.get('emergencia_usuario_nombre', 'Empleado')

        if not perfil_id:
            return JsonResponse({
                'success': False,
                'mensaje': 'Sesión de emergencia expirada. Vuelve a ingresar tu código.'
            }, status=403)

        data = json.loads(request.body)
        nino_id = data.get('nino_id')
        observacion = str(data.get('observacion', '')).strip()

        if not nino_id:
            return JsonResponse({'success': False, 'mensaje': 'Falta el ID del niño.'}, status=400)

        nino = get_object_or_404(Nino, id=nino_id, activo=True)

        ultimo = RegistroAcceso.objects.filter(nino=nino).order_by('-fecha_hora').first()
        if not ultimo or ultimo.tipo != 'ENTRADA':
            return JsonResponse({
                'success': False,
                'mensaje': f'{nino.nombre_completo()} no está dentro actualmente.'
            }, status=400)

        # Obtener el usuario que validó el código (desde la sesión)
        try:
            perfil_obj = Perfil.objects.get(id=perfil_id)
            empleado_user = perfil_obj.user
        except Perfil.DoesNotExist:
            empleado_user = request.user if request.user.is_authenticated else None

        registro = RegistroAcceso.objects.create(
            nino=nino,
            tutor=None,
            tipo='SALIDA',
            verificacion_exitosa=True,
            metodo_verificacion='EMERGENCIA',
            registrado_por=empleado_user,
            observaciones=observacion if observacion else None,
        )

        # Limpiar sesión de emergencia
        request.session.pop('emergencia_perfil_id', None)
        request.session.pop('emergencia_usuario_nombre', None)

        return JsonResponse({
            'success': True,
            'mensaje': f'Salida de emergencia registrada para {nino.nombre_completo()}.',
            'registro_id': registro.id,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': f'Error: {str(e)}'}, status=500)


# ============================================
# COLONIAS Y RESPALDO (Desde Main)
# ============================================

@login_required
def lista_colonias(request):
    colonias = Colonia.objects.all().order_by('d_codigo', 'd_asenta')
    return render(request, 'guarderia/colonias/lista.html', {
        'colonias': colonias,
    })

@login_required
def crear_colonia(request):
    """Crear una colonia personalizada"""
    if request.method == 'POST':
        form = ColoniaForm(request.POST)
        if form.is_valid():
            colonia = form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Colonia "{colonia.d_asenta}" creada correctamente.',
                    'redirect_url': '/guarderia/colonias/'
                })
            messages.success(request, f'Colonia "{colonia.d_asenta}" creada correctamente.')
            return redirect('guarderia:lista_colonias')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = ColoniaForm()

    return render(request, 'guarderia/colonias/form.html', {
        'form': form,
        'titulo': 'Nueva Colonia',
        'accion': 'Registrar',
    })

@login_required
def editar_colonia(request, pk):
    """Editar una colonia existente"""
    colonia = get_object_or_404(Colonia, pk=pk)
    if request.method == 'POST':
        form = ColoniaForm(request.POST, instance=colonia)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Colonia "{colonia.d_asenta}" actualizada correctamente.',
                    'redirect_url': '/guarderia/colonias/'
                })
            messages.success(request, f'Colonia "{colonia.d_asenta}" actualizada.')
            return redirect('guarderia:lista_colonias')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = ColoniaForm(instance=colonia)

    return render(request, 'guarderia/colonias/form.html', {
        'form': form,
        'colonia': colonia,
        'titulo': f'Editar — {colonia.d_asenta}',
        'accion': 'Guardar Cambios',
    })

@login_required
def eliminar_colonia(request, pk):
    """Eliminar colonia (solo POST/AJAX)"""
    colonia = get_object_or_404(Colonia, pk=pk)
    if request.method == 'POST':
        nombre = colonia.d_asenta
        colonia.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Colonia "{nombre}" eliminada.'})
        messages.success(request, f'Colonia "{nombre}" eliminada.')
        return redirect('guarderia:lista_colonias')
    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

@login_required
def descargar_respaldo_db(request):
    """Genera y descarga un respaldo PostgreSQL"""
    if not (request.user.is_superuser or
            (hasattr(request.user, 'perfil') and 
             request.user.perfil.rol.nombre == 'ADMIN')):
        return JsonResponse({'error': 'No tienes permisos.'}, status=403)

    db    = settings.DATABASES['default']
    fecha = datetime.now().strftime('%Y%m%d_%H%M%S')

    pg_dump_path = shutil.which('pg_dump')

    if not pg_dump_path:
        rutas_windows = [
            r'C:\Program Files\PostgreSQL\17\bin\pg_dump.exe',
            r'C:\Program Files\PostgreSQL\16\bin\pg_dump.exe',
            r'C:\Program Files\PostgreSQL\15\bin\pg_dump.exe',
            r'C:\Program Files\PostgreSQL\14\bin\pg_dump.exe',
            r'C:\Program Files\PostgreSQL\13\bin\pg_dump.exe',
        ]
        for ruta in rutas_windows:
            if os.path.exists(ruta):
                pg_dump_path = ruta
                break

    if not pg_dump_path:
        return HttpResponse(
            '<h2>Error: pg_dump no encontrado</h2>'
            '<p>Verifica que PostgreSQL esté instalado y pg_dump esté en el PATH.</p>',
            status=500,
            content_type='text/html'
        )

    try:
        env = os.environ.copy()
        env['PGPASSWORD'] = db.get('PASSWORD', '')

        host = db.get('HOST', 'localhost') or 'localhost'
        port = str(db.get('PORT', 5432) or 5432)
        user = db.get('USER', 'postgres')
        name = db.get('NAME', 'proyecto')

        cmd = [
            pg_dump_path, '-h', host, '-p', port, '-U', user, '-d', name,
            '--no-password', '-F', 'p', '-E', 'UTF8',
        ]

        resultado = subprocess.run(cmd, capture_output=True, env=env, timeout=120)

        if resultado.returncode != 0:
            error_msg = resultado.stderr.decode('utf-8', errors='replace')
            return HttpResponse(
                f'<h2>Error de pg_dump</h2><pre>{error_msg}</pre>',
                status=500,
                content_type='text/html'
            )

        nombre_archivo = f'respaldo_guarderia_{fecha}.sql'
        response = HttpResponse(resultado.stdout, content_type='application/sql')
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        return response

    except Exception as e:
        import traceback
        return HttpResponse(f'<h2>Error</h2><pre>{traceback.format_exc()}</pre>', status=500)

@login_required
def pagina_respaldo(request):
    if not (request.user.is_superuser or
            (hasattr(request.user, 'perfil') and 
             request.user.perfil.rol.nombre == 'ADMIN')):
        return redirect('guarderia:dashboard')
    return render(request, 'guarderia/respaldo.html')
