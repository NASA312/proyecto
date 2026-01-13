from django.contrib import admin
from .models import Tutor, Nino, RegistroAcceso

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