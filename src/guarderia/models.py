from django.db import models
from django.utils import timezone

class Tutor(models.Model):
    """Modelo para padres/tutores autorizados a recoger niños"""
    # Información personal
    nombre = models.CharField(max_length=100, help_text="Nombre completo del tutor")
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100, blank=True, null=True)
    
    # Información de contacto
    telefono = models.CharField(max_length=20)
    telefono_emergencia = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    
    # Identificación
    TIPO_ID_CHOICES = [
        ('INE', 'INE/IFE'),
        ('PASAPORTE', 'Pasaporte'),
        ('LICENCIA', 'Licencia de Conducir'),
        ('OTRO', 'Otro'),
    ]
    tipo_identificacion = models.CharField(max_length=20, choices=TIPO_ID_CHOICES, default='INE')
    numero_identificacion = models.CharField(max_length=50, unique=True)
    
    # Relación con el niño
    PARENTESCO_CHOICES = [
        ('PADRE', 'Padre'),
        ('MADRE', 'Madre'),
        ('ABUELO', 'Abuelo/a'),
        ('TIO', 'Tío/a'),
        ('TUTOR', 'Tutor Legal'),
        ('OTRO', 'Otro'),
    ]
    parentesco = models.CharField(max_length=20, choices=PARENTESCO_CHOICES)
    
    # Datos biométricos
    huella_template = models.BinaryField(blank=True, null=True, help_text="Template biométrico de la huella")
    huella_imagen = models.ImageField(upload_to='huellas_tutores/', blank=True, null=True)
    huella_registrada = models.BooleanField(default=False)
    fecha_registro_huella = models.DateTimeField(blank=True, null=True)
    
    # Estado y control
    activo = models.BooleanField(default=True, help_text="Tutor autorizado para recoger niños")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    # Observaciones
    notas = models.TextField(blank=True, null=True, help_text="Notas adicionales sobre el tutor")
    
    class Meta:
        verbose_name = "Tutor Autorizado"
        verbose_name_plural = "Tutores Autorizados"
        ordering = ['apellido_paterno', 'apellido_materno', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno or ''}".strip()
    
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno or ''}".strip()


class Nino(models.Model):
    """Modelo para los niños de la guardería"""
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField()
    
    # Foto del niño
    foto = models.ImageField(upload_to='fotos_ninos/', blank=True, null=True)
    
    # Relación con tutores
    tutores = models.ManyToManyField(Tutor, related_name='ninos', 
                                     help_text="Tutores autorizados a recoger este niño")
    
    # Información adicional
    alergias = models.TextField(blank=True, null=True)
    medicamentos = models.TextField(blank=True, null=True)
    tipo_sangre = models.CharField(max_length=5, blank=True, null=True, help_text="Ej: O+, A-, AB+")
    grupo = models.CharField(max_length=50, blank=True, null=True, help_text="Grupo o salón")
    activo = models.BooleanField(default=True)
    
    fecha_ingreso = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Niño"
        verbose_name_plural = "Niños"
        ordering = ['apellido_paterno', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno}"
    
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno or ''}".strip()
    
    def edad(self):
        from datetime import date
        today = date.today()
        return today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )


class RegistroAcceso(models.Model):
    """Registro de entrada/salida de niños"""
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
    ]
    
    nino = models.ForeignKey(Nino, on_delete=models.CASCADE, related_name='registros')
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='registros')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    
    # Verificación
    verificacion_exitosa = models.BooleanField(default=True)
    metodo_verificacion = models.CharField(max_length=20, default='HUELLA')
    
    # Observaciones
    observaciones = models.TextField(blank=True, null=True)
    
    # Registrado por (trabajador)
    registrado_por = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='registros_guardados'
    )
    
    class Meta:
        verbose_name = "Registro de Acceso"
        verbose_name_plural = "Registros de Acceso"
        ordering = ['-fecha_hora']
    
    def __str__(self):
        return f"{self.tipo} - {self.nino} por {self.tutor} ({self.fecha_hora.strftime('%d/%m/%Y %H:%M')})"