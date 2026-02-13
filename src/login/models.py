from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Rol(models.Model):
    """Roles del sistema para control de permisos"""
    ADMINISTRADOR = 'ADMIN'
    OBSERVADOR = 'OBSERVADOR'
    EMPLEADO = 'EMPLEADO'
    
    ROLES_CHOICES = [
        (ADMINISTRADOR, 'Administrador'),
        (OBSERVADOR, 'Observador'),
        (EMPLEADO, 'Empleado'),
    ]
    
    nombre = models.CharField(
        max_length=20,
        choices=ROLES_CHOICES,
        unique=True,
        help_text="Nombre del rol en el sistema"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        help_text="Descripción de las funciones del rol"
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ['nombre']
    
    def __str__(self):
        return self.get_nombre_display()


class Perfil(models.Model):
    """Perfil extendido para trabajadores del sistema"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil',
        help_text="Usuario de Django asociado"
    )
    rol = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        related_name='perfiles',
        null=True,
        blank=True,
        help_text="Rol asignado al usuario"
    )
    
    # Información personal
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Teléfono de contacto"
    )
    fecha_nacimiento = models.DateField(
        blank=True,
        null=True,
        help_text="Fecha de nacimiento"
    )
    direccion = models.TextField(
        blank=True,
        null=True,
        help_text="Dirección completa"
    )
    
    # Foto de perfil
    foto_perfil = models.ImageField(
        upload_to='fotos_usuarios/',
        blank=True,
        null=True,
        help_text="Foto de perfil del usuario"
    )
    
    # Información laboral
    cargo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Puesto en la institución"
    )
    numero_empleado = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        help_text="Número de empleado institucional"
    )
    fecha_ingreso = models.DateField(
        blank=True,
        null=True,
        help_text="Fecha de ingreso a la institución"
    )
    
    # Datos biométricos (para futuro)
    huella_registrada = models.BooleanField(
        default=False,
        help_text="Indica si tiene huella registrada"
    )
    fecha_registro_huella = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha de registro de huella"
    )
    
    # Control de estado
    activo = models.BooleanField(
        default=True,
        help_text="Usuario activo en el sistema"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    # Notas adicionales
    notas = models.TextField(
        blank=True,
        null=True,
        help_text="Observaciones sobre el usuario"
    )
    
    class Meta:
        verbose_name = "Perfil de Trabajador"
        verbose_name_plural = "Perfiles de Trabajadores"
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.rol or 'Sin rol'}"
    
    def nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        return self.user.get_full_name() or self.user.username
    
    def tiene_rol(self, rol_nombre):
        """Verifica si el usuario tiene un rol específico"""
        return self.rol and self.rol.nombre == rol_nombre
    
    def es_administrador(self):
        """Verifica si el usuario es administrador"""
        return self.tiene_rol(Rol.ADMINISTRADOR)
    
    def es_observador(self):
        """Verifica si el usuario es observador"""
        return self.tiene_rol(Rol.OBSERVADOR)
    
    def es_empleado(self):
        """Verifica si el usuario es empleado"""
        return self.tiene_rol(Rol.EMPLEADO)


# ============================================
# SIGNALS - Creación automática de perfil
# ============================================

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crea automáticamente un perfil cuando se crea un usuario"""
    if created:
        Perfil.objects.create(user=instance)


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """Guarda el perfil cuando se guarda el usuario"""
    if hasattr(instance, 'perfil'):
        instance.perfil.save()