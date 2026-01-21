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


@admin.register(ObservacionNino)
class ObservacionNinoAdmin(admin.ModelAdmin):
    list_display = ['nino', 'tipo', 'fecha', 'hora', 'importante', 'notificar_tutor', 'notificado', 'registrado_por']
    search_fields = ['nino__nombre', 'nino__apellido_paterno', 'descripcion']
    list_filter = ['tipo', 'importante', 'notificar_tutor', 'notificado', 'fecha']
    date_hierarchy = 'fecha'
    readonly_fields = ['fecha_notificacion', 'hora']
    
    fieldsets = (
        ('Información General', {
            'fields': ('nino', 'tipo', 'fecha')
        }),
        ('Observación', {
            'fields': ('descripcion', 'importante')
        }),
        ('Notificación', {
            'fields': ('notificar_tutor', 'notificado', 'fecha_notificacion')
        }),
        ('Registro', {
            'fields': ('registrado_por', 'hora'),
            'classes': ('collapse',)
        }),
    )
