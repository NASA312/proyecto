from django.contrib import admin
from .models import *

@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'telefono', 'parentesco', 'huella_registrada', 'activo']
    list_filter = ['activo', 'huella_registrada', 'parentesco']
    search_fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'numero_identificacion']
    readonly_fields = ['fecha_registro', 'fecha_modificacion']

@admin.register(Nino)
class NinoAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'edad', 'grupo', 'activo']
    list_filter = ['activo', 'grupo']
    search_fields = ['nombre', 'apellido_paterno', 'apellido_materno']
    filter_horizontal = ['tutores']

@admin.register(RegistroAcceso)
class RegistroAccesoAdmin(admin.ModelAdmin):
    list_display = ['nino', 'tutor', 'tipo', 'fecha_hora', 'verificacion_exitosa']
    list_filter = ['tipo', 'verificacion_exitosa', 'fecha_hora']
    search_fields = ['nino__nombre', 'tutor__nombre']
    date_hierarchy = 'fecha_hora'
    
@admin.register(ServicioMedico)
class ServicioMedicoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'siglas', 'activo', 'fecha_registro']
    search_fields = ['nombre', 'siglas']
    list_filter = ['activo']


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'grado', 'capacidad_maxima', 'ninos_asignados', 'activo']
    search_fields = ['nombre', 'grado']
    list_filter = ['tipo', 'activo']
    
    def ninos_asignados(self, obj):
        return obj.ninos_asignados()
    ninos_asignados.short_description = 'Niños Asignados'


@admin.register(AreaObservacion)
class AreaObservacionAdmin(admin.ModelAdmin):
    list_display       = ['orden', 'nombre', 'descripcion', 'activo']
    list_display_links = ['nombre']
    list_editable      = ['orden', 'activo']
    search_fields      = ['nombre']
    list_filter        = ['activo']
    ordering           = ['orden', 'nombre']


@admin.register(ObservacionNino)
class ObservacionNinoAdmin(admin.ModelAdmin):
    list_display  = ['nino', 'area', 'tipo', 'fecha', 'es_recurrente', 'atendida', 'importante', 'registrado_por']
    search_fields = ['nino__nombre', 'nino__apellido_paterno', 'descripcion']
    list_filter   = ['area', 'tipo', 'es_recurrente', 'atendida', 'importante', 'notificar_tutor', 'fecha']
    date_hierarchy = 'fecha'
    readonly_fields = ['fecha_notificacion', 'hora', 'fecha_atendida', 'atendida_por']

    fieldsets = (
        ('Información General', {
            'fields': ('nino', 'area', 'tipo', 'fecha')
        }),
        ('Observación', {
            'fields': ('descripcion', 'importante')
        }),
        ('Recurrencia', {
            'fields': ('es_recurrente', 'atendida', 'fecha_atendida', 'atendida_por'),
            'description': 'Configuración para observaciones que persisten hasta ser atendidas'
        }),
        ('Notificación', {
            'fields': ('notificar_tutor', 'notificado', 'fecha_notificacion')
        }),
        ('Registro', {
            'fields': ('registrado_por', 'hora'),
            'classes': ('collapse',)
        }),
    )
