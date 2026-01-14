from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import Tutor, Nino, RegistroAcceso
from .forms import TutorForm, NinoForm, AsignarTutorForm
import base64
import json
import requests
from django.db.models import Q 

# ============================================
# VISTAS DE TUTORES
# ============================================

@login_required
def lista_tutores(request):
    """Lista de tutores registrados"""
    tutores = Tutor.objects.filter(activo=True).order_by('-fecha_registro')
    ctx = {'tutores': tutores}
    return render(request, 'guarderia/tutores/lista.html', ctx)

@login_required
def registrar_tutor(request):
    """Registrar nuevo tutor"""
    if request.method == 'POST':
        form = TutorForm(request.POST)
        
        # Detectar si es petición AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if form.is_valid():
            tutor = form.save()
            
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
    
    return render(request, 'guarderia/tutores/editar.html', {'form': form, 'tutor': tutor})

@login_required
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
    ninos = Nino.objects.filter(activo=True).order_by('grupo', 'apellido_paterno')
    ctx = {'ninos': ninos}
    return render(request, 'guarderia/ninos/lista.html', ctx)

@login_required
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
    
    ctx = {
        'nino': nino,
        'tutores': tutores,
        'registros': registros
    }
    return render(request, 'guarderia/ninos/detalle.html', ctx)

@login_required
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
def historial_accesos(request):
    """Historial de entradas y salidas"""
    registros = RegistroAcceso.objects.all().select_related('nino', 'tutor').order_by('-fecha_hora')[:100]
    ctx = {'registros': registros}
    return render(request, 'guarderia/registros/historial.html', ctx)

@csrf_exempt
def registrar_salida(request):
    """Registrar salida después de verificar huella"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nino_id = data.get('nino_id')
            tutor_id = data.get('tutor_id')
            
            if nino_id and tutor_id:
                nino = Nino.objects.get(id=nino_id)
                tutor = Tutor.objects.get(id=tutor_id)
                
                # Verificar que el tutor esté autorizado
                if tutor in nino.tutores.all():
                    registro = RegistroAcceso.objects.create(
                        nino=nino,
                        tutor=tutor,
                        tipo='SALIDA',
                        verificacion_exitosa=True,
                        metodo_verificacion='HUELLA'
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'mensaje': f'{nino.nombre_completo()} entregado a {tutor.nombre_completo()}'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'mensaje': 'Este tutor no está autorizado para recoger a este niño'
                    })
        except Exception as e:
            return JsonResponse({'success': False, 'mensaje': str(e)})
    
    return JsonResponse({'success': False, 'mensaje': 'Método no permitido'}, status=405)

# ============================================
# APIs para .NET - MÉTODO DE CONSULTA
# ============================================

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