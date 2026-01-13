from django.contrib import admin
from .models import Perfil

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ['user', 'telefono', 'cargo']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    list_filter = ['cargo']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Información Personal', {
            'fields': ('telefono', 'fecha_nacimiento', 'direccion')
        }),
        ('Información Laboral', {
            'fields': ('cargo',)
        }),
    )