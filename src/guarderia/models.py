from django.db import models
from django.utils import timezone
from django.conf import settings

class Dependencia(models.Model):
    """Dependencias de gobierno"""
    nombre = models.CharField(max_length=200, unique=True)
    siglas = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Dependencia"
        verbose_name_plural = "Dependencias"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.siglas} - {self.nombre}" if self.siglas else self.nombre


class Departamento(models.Model):
    """Departamentos dentro de las dependencias"""
    dependencia = models.ForeignKey(Dependencia, on_delete=models.CASCADE, related_name='departamentos')
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['dependencia', 'nombre']
        unique_together = ['dependencia', 'nombre']
    
    def __str__(self):
        return f"{self.dependencia.siglas or self.dependencia.nombre} - {self.nombre}"


# models.py
class Colonia(models.Model):
    """Colonias por código postal"""
    d_codigo = models.CharField(max_length=5, db_index=True, verbose_name="Código Postal", default='00000')
    d_asenta = models.CharField(max_length=200, verbose_name="Nombre del Asentamiento", default='Sin nombre')
    D_mnpio = models.CharField(max_length=200, verbose_name="Municipio", default="Sin municipio")
    d_estado = models.CharField(max_length=100, verbose_name="Estado", default="Sin estado")

    class Meta:
        verbose_name = "Colonia"
        verbose_name_plural = "Colonias"
        ordering = ['d_codigo', 'd_asenta']
        indexes = [
            models.Index(fields=['d_codigo']),
            models.Index(fields=['d_codigo', 'd_asenta']),
        ]

    def __str__(self):
        return f"{self.d_asenta} - CP {self.d_codigo}"


# ⭐ NUEVO MODELO ⭐
class ServicioMedico(models.Model):
    """Servicios médicos disponibles (ISSSTE, IMSS, etc.)"""
    nombre = models.CharField(max_length=100, unique=True)
    siglas = models.CharField(max_length=20, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Servicio Médico"
        verbose_name_plural = "Servicios Médicos"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.siglas} - {self.nombre}" if self.siglas else self.nombre


# ⭐ NUEVO MODELO ⭐
class Grupo(models.Model):
    """Grupos/Salones de la guardería"""
    TIPO_GRUPO_CHOICES = [
        ('LACTANTE', 'Lactante'),
        ('MATERNAL', 'Maternal'),
        ('PREESCOLAR', 'Preescolar'),
    ]
    
    nombre = models.CharField(max_length=100, help_text="Ej: Grupo A, Sala 1")
    tipo = models.CharField(max_length=20, choices=TIPO_GRUPO_CHOICES)
    grado = models.CharField(max_length=50, help_text="Ej: 1er año, 2do año")
    capacidad_maxima = models.PositiveIntegerField(default=20, help_text="Número máximo de niños")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Grupo"
        verbose_name_plural = "Grupos"
        ordering = ['tipo', 'grado', 'nombre']
        unique_together = ['nombre', 'tipo', 'grado']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.grado} - {self.nombre}"
    
    def ninos_asignados(self):
        """Retorna la cantidad de niños asignados"""
        return self.ninos.filter(activo=True).count()
    
    def capacidad_disponible(self):
        """Retorna cuántos lugares quedan disponibles"""
        return self.capacidad_maxima - self.ninos_asignados()
    
    def esta_lleno(self):
        """Verifica si el grupo está lleno"""
        return self.ninos_asignados() >= self.capacidad_maxima
    
    def porcentaje_ocupacion(self):
        """Retorna el porcentaje de ocupación"""
        if self.capacidad_maxima == 0:
            return 0
        return round((self.ninos_asignados() / self.capacidad_maxima) * 100, 1)


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
    
    # Dirección
    codigo_postal = models.CharField(max_length=5, blank=True, null=True)
    colonia = models.ForeignKey(Colonia, on_delete=models.SET_NULL, null=True, blank=True)
    calle = models.CharField(max_length=200, blank=True, null=True)
    numero_exterior = models.CharField(max_length=20, blank=True, null=True)
    numero_interior = models.CharField(max_length=20, blank=True, null=True)
    referencias = models.TextField(blank=True, null=True, help_text="Referencias para llegar")
    
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
    
    # ⭐ NUEVOS CAMPOS - Servicio Médico ⭐
    servicio_medico = models.ForeignKey(
        ServicioMedico, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='tutores',
        help_text="Servicio médico del tutor (ISSSTE, IMSS, etc.)"
    )
    numero_seguro_social = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Número de seguro social (NSS)"
    )
    
    # Información laboral
    es_trabajador = models.BooleanField(default=False, help_text="¿Es trabajador de gobierno?")
    dependencia = models.ForeignKey(Dependencia, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='trabajadores')
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='trabajadores')
    
    ESTATUS_LABORAL_CHOICES = [
        ('ALTA', 'Alta'),
        ('BAJA', 'Baja'),
    ]
    estatus_laboral = models.CharField(max_length=10, choices=ESTATUS_LABORAL_CHOICES, 
                                      blank=True, null=True)
    numero_empleado = models.CharField(max_length=50, blank=True, null=True)
    fecha_alta = models.DateField(blank=True, null=True)
    fecha_baja = models.DateField(blank=True, null=True)
    
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
    
    def direccion_completa(self):
        """Retorna la dirección completa formateada"""
        partes = []
        if self.calle:
            direccion = self.calle
            if self.numero_exterior:
                direccion += f" #{self.numero_exterior}"
            if self.numero_interior:
                direccion += f" Int. {self.numero_interior}"
            partes.append(direccion)
        
        if self.colonia:
            partes.append(f"Col. {self.colonia.nombre}")
            partes.append(f"{self.colonia.municipio}, {self.colonia.estado}")
            partes.append(f"CP {self.colonia.codigo_postal}")
        
        return ", ".join(partes) if partes else "Sin dirección"


class Nino(models.Model):
    """Modelo para los niños de la guardería"""
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField()
    
    # Número de matrícula (único, obligatorio)
    numero_matricula = models.CharField(
        max_length=20,
        unique=True,
        null=True,   # 👈 importante
        blank=True
    )
    
    # Género del niño
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]
    genero = models.CharField(
        max_length=1,
        choices=GENERO_CHOICES,
        default='M',
        help_text="Género del niño"
    )
    
    # Foto del niño
    foto = models.ImageField(upload_to='fotos_ninos/', blank=True, null=True)
    
    # Relación con tutores
    tutores = models.ManyToManyField(Tutor, related_name='ninos', 
                                     help_text="Tutores autorizados a recoger este niño")
    
    # Información adicional
    alergias = models.TextField(blank=True, null=True)
    medicamentos = models.TextField(blank=True, null=True)
    tipo_sangre = models.CharField(max_length=5, blank=True, null=True, help_text="Ej: O+, A-, AB+")
    
    # ⭐ MODIFICADO: grupo ahora es ForeignKey ⭐
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ninos',
        help_text="Grupo al que pertenece el niño"
    )
    
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


# ⭐ NUEVO MODELO ⭐
class ObservacionNino(models.Model):
    """Observaciones diarias sobre los niños"""
    TIPO_OBSERVACION_CHOICES = [
        ('GENERAL', 'General'),
        ('CONDUCTA', 'Conducta'),
        ('SALUD', 'Salud'),
        ('HIGIENE', 'Higiene'),
        ('MATERIAL', 'Material/Uniforme'),
        ('ALIMENTACION', 'Alimentación'),
        ('ACADEMICO', 'Académico'),
        ('OTRO', 'Otro'),
    ]
    
    nino = models.ForeignKey(
        Nino,
        on_delete=models.CASCADE,
        related_name='observaciones',
        help_text="Niño al que se refiere la observación"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_OBSERVACION_CHOICES,
        default='GENERAL',
        help_text="Tipo de observación"
    )
    descripcion = models.TextField(
        help_text="Descripción detallada de la observación"
    )
    fecha = models.DateField(
        default=timezone.now,
        help_text="Fecha de la observación"
    )
    hora = models.TimeField(
        auto_now_add=True,
        help_text="Hora de registro"
    )
    registrado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='observaciones_registradas',
        help_text="Usuario que registró la observación"
    )
    importante = models.BooleanField(
        default=False,
        help_text="Marcar si requiere atención especial"
    )
    notificar_tutor = models.BooleanField(
        default=False,
        help_text="Si se debe notificar al tutor"
    )
    notificado = models.BooleanField(
        default=False,
        help_text="Si ya se notificó al tutor"
    )
    fecha_notificacion = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha y hora en que se notificó"
    )
    
    class Meta:
        verbose_name = "Observación"
        verbose_name_plural = "Observaciones"
        ordering = ['-fecha', '-hora']
        indexes = [
            models.Index(fields=['nino', '-fecha']),
            models.Index(fields=['fecha', 'importante']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.nino.nombre_completo()} - {self.fecha}"


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
    
class ConfiguracionGuarderia(models.Model):

    nombre = models.CharField(max_length=200, default='Mi Guardería')
    
    # Tiempo mínimo entre registros del mismo niño (en minutos)
    tiempo_minimo_entre_registros = models.PositiveIntegerField(
        default=30,
        verbose_name='Tiempo mínimo entre registros (minutos)',
        help_text='Minutos que deben pasar entre una entrada y una salida, o viceversa, para el mismo niño.'
    )
    
    # Metadata
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='configuraciones_actualizadas'
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)
 
    class Meta:
        verbose_name = 'Configuración de Guardería'
        verbose_name_plural = 'Configuración de Guardería'
 
    def __str__(self):
        return f'Configuración – {self.tiempo_minimo_entre_registros} min entre registros'
 
    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj