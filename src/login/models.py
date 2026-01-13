from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Perfil(models.Model):
    """Perfil para trabajadores del sistema"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    cargo = models.CharField(max_length=100, blank=True, null=True, help_text="Puesto en la empresa")
    
    def __str__(self):
        return f"Perfil de {self.user.username}"
    
    class Meta:
        verbose_name = "Perfil de Trabajador"
        verbose_name_plural = "Perfiles de Trabajadores"

# Signal para crear automáticamente el perfil
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    if hasattr(instance, 'perfil'):
        instance.perfil.save()