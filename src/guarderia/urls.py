from django.urls import path
from . import views

app_name = 'guarderia'

urlpatterns = [
    # =====================================
    # DASHBOARD
    # =====================================
    path('', views.dashboard, name='dashboard'),
    
    # =====================================
    # TUTORES
    # =====================================
    path('tutores/', views.lista_tutores, name='lista_tutores'),
    path('tutores/registrar/', views.registrar_tutor, name='registrar_tutor'),
    path('tutores/<int:tutor_id>/', views.detalle_tutor, name='detalle_tutor'),
    path('tutores/<int:tutor_id>/editar/', views.editar_tutor, name='editar_tutor'),
    path('tutores/<int:tutor_id>/huella/', views.registrar_huella_tutor, name='registrar_huella_tutor'),
    path('tutores/buscar/', views.buscar_tutores_ajax, name='buscar_tutores_ajax'),

    # =====================================
    # NIÑOS
    # =====================================
    path('ninos/', views.lista_ninos, name='lista_ninos'),
    path('ninos/registrar/', views.registrar_nino, name='registrar_nino'),
    path('ninos/<int:nino_id>/', views.detalle_nino, name='detalle_nino'),
    path('ninos/<int:nino_id>/editar/', views.editar_nino, name='editar_nino'),
    path('ninos/<int:nino_id>/asignar-tutores/', views.asignar_tutores, name='asignar_tutores'),
    path('ninos/<int:nino_id>/observaciones/', views.observaciones_nino, name='observaciones_nino'),  # ⭐ CORREGIDO

    # =====================================
    # VERIFICACIÓN PÚBLICA
    # =====================================
    path('verificar-huella/', views.verificar_huella_tutor, name='verificar_huella_tutor'),
    path('verificar-huella-inicio/', views.verificar_huella_inicio, name='verificar_huella_inicio'),
    path('verificar-huella-estado/', views.verificar_huella_estado, name='verificar_huella_estado'),

    # =====================================
    # REGISTROS
    # =====================================
    path('registros/historial/', views.historial_accesos, name='historial_accesos'),
    path('registros/salida/', views.registrar_salida, name='registrar_salida'),
    path('registrar-entrada/', views.registrar_entrada, name='registrar_entrada'),


    # =====================================
    # APIs HUELLAS
    # =====================================
    path('api/huella/tutor/<int:tutor_id>/verificar/', views.verificar_huella_capturada_tutor, name='verificar_huella_capturada_tutor'),
    path('api/huella/tutor/<int:tutor_id>/estado/', views.verificar_estado_huella, name='verificar_estado_huella'),
    
    # API para obtener estado de niño (DENTRO/FUERA)
    path('api/nino/<int:nino_id>/estado/', views.obtener_estado_nino, name='obtener_estado_nino'),
    path('api/buscar-nino/', views.buscar_nino_por_matricula, name='buscar_nino_por_matricula'),
    
    # =====================================
    # COLONIAS
    # =====================================
    path('api/colonias/buscar/', views.buscar_colonias_cp, name='buscar_colonias'),

    # =====================================
    # DEPENDENCIAS
    # =====================================
    path('dependencias/', views.lista_dependencias, name='lista_dependencias'),
    path('dependencias/registrar/', views.registrar_dependencia, name='registrar_dependencia'),
    path('dependencias/<int:dependencia_id>/editar/', views.editar_dependencia, name='editar_dependencia'),  # ⭐ NUEVO
    
    # =====================================
    # DEPARTAMENTOS
    # =====================================
    path('departamentos/', views.lista_departamentos, name='lista_departamentos'),  # ⭐ NUEVO
    path('departamentos/registrar/', views.registrar_departamento, name='registrar_departamento'),
    path('departamentos/<int:departamento_id>/editar/', views.editar_departamento, name='editar_departamento'),  # ⭐ NUEVO
    path('api/departamentos/', views.obtener_departamentos_ajax, name='obtener_departamentos_ajax'),
    
    # =====================================
    # SERVICIOS MÉDICOS
    # =====================================
    path('servicios-medicos/', views.lista_servicios_medicos, name='lista_servicios_medicos'),
    path('servicios-medicos/registrar/', views.registrar_servicio_medico, name='registrar_servicio_medico'),
    path('servicios-medicos/<int:servicio_id>/editar/', views.editar_servicio_medico, name='editar_servicio_medico'),
    
    # =====================================
    # GRUPOS
    # =====================================
    path('grupos/', views.lista_grupos, name='lista_grupos'),
    path('grupos/registrar/', views.registrar_grupo, name='registrar_grupo'),
    path('grupos/<int:grupo_id>/', views.detalle_grupo, name='detalle_grupo'),
    path('grupos/<int:grupo_id>/editar/', views.editar_grupo, name='editar_grupo'),
    path('api/grupos/disponibles/', views.obtener_grupos_disponibles_ajax, name='obtener_grupos_disponibles_ajax'),
    
    # =====================================
    # OBSERVACIONES
    # =====================================
    path('observaciones/', views.lista_observaciones, name='lista_observaciones'),
    path('observaciones/registrar/', views.registrar_observacion, name='registrar_observacion'),
    path('observaciones/<int:observacion_id>/editar/', views.editar_observacion, name='editar_observacion'),
    path('observaciones/<int:observacion_id>/notificar/', views.marcar_observacion_notificada, name='marcar_observacion_notificada'),
        # ========== PAPELERA DEPARTAMENTOS ==========
    path('departamentos/<int:departamento_id>/enviar-papelera/', 
         views.enviar_departamento_papelera, 
         name='enviar_departamento_papelera'),
    
    path('departamentos/<int:departamento_id>/restaurar/', 
         views.restaurar_departamento, 
         name='restaurar_departamento'),
    
    # ========== PAPELERA DEPENDENCIAS ==========
    path('dependencias/<int:dependencia_id>/enviar-papelera/', 
         views.enviar_dependencia_papelera, 
         name='enviar_dependencia_papelera'),
    
    path('dependencias/<int:dependencia_id>/restaurar/', 
         views.restaurar_dependencia, 
         name='restaurar_dependencia'),
    
    # Servicios Médicos
     path('servicios-medicos/<int:servicio_id>/enviar-papelera/',
          views.enviar_servicio_papelera, name='enviar_servicio_papelera'),
     path('servicios-medicos/<int:servicio_id>/restaurar/',
          views.restaurar_servicio, name='restaurar_servicio'),

     # Grupos
     path('grupos/<int:grupo_id>/enviar-papelera/',
          views.enviar_grupo_papelera, name='enviar_grupo_papelera'),
     path('grupos/<int:grupo_id>/restaurar/',
          views.restaurar_grupo, name='restaurar_grupo'),

     # Tutores
     path('tutores/<int:tutor_id>/enviar-papelera/',
          views.enviar_tutor_papelera, name='enviar_tutor_papelera'),
     path('tutores/<int:tutor_id>/restaurar/',
          views.restaurar_tutor, name='restaurar_tutor'),

     # Niños
     path('ninos/<int:nino_id>/enviar-papelera/',
          views.enviar_nino_papelera, name='enviar_nino_papelera'),
     path('ninos/<int:nino_id>/restaurar/',
          views.restaurar_nino, name='restaurar_nino'),

     path('grupos/finalizar-ciclo/', 
     views.finalizar_ciclo_escolar, 
     name='finalizar_ciclo_escolar'),
    
    path('reportes/tutores-dependencia/', views.reporte_tutores_dependencia, name='reporte_tutores_dependencia'),
    path('reportes/asistencia-genero/',   views.reporte_asistencia_genero,   name='reporte_asistencia_genero'),
    path('configuracion/tiempo-limite/', views.configuracion_guarderia, name='configuracion_guarderia'),
]