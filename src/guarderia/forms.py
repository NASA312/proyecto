from django import forms
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class TutorForm(forms.ModelForm):
    """Formulario para registrar tutores/padres"""
    
    # Campo personalizado para búsqueda dinámica de colonias
    buscar_colonia = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar colonia...',
            'disabled': 'disabled'
        }),
        label="Buscar Colonia"
    )
    
    class Meta:
        model = Tutor
        fields = [
            'nombre', 'apellido_paterno', 'apellido_materno',
            'telefono', 'telefono_emergencia', 'email',
            'codigo_postal', 'colonia', 'calle', 'numero_exterior', 
            'numero_interior', 'referencias',
            'tipo_identificacion', 'numero_identificacion',
            'parentesco',
            'servicio_medico', 'numero_seguro_social',  # ⭐ NUEVOS ⭐
            'es_trabajador', 'dependencia', 'departamento', 
            'estatus_laboral', 'numero_empleado', 'fecha_alta', 'fecha_baja',
            'notas'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre(s)'}),
            'apellido_paterno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido Paterno'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido Materno'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(123) 456-7890'}),
            'telefono_emergencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono de emergencia'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            
            # Dirección
            'codigo_postal': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '12345',
                'maxlength': '5',
                'pattern': '[0-9]{5}',
                'id': 'id_codigo_postal'
            }),
            'colonia': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_colonia',
                'disabled': 'disabled'
            }),
            'calle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la calle'}),
            'numero_exterior': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'No. Ext.'}),
            'numero_interior': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'No. Int. (opcional)'}),
            'referencias': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Referencias para llegar'}),
            
            # Identificación
            'tipo_identificacion': forms.Select(attrs={'class': 'form-control'}),
            'numero_identificacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de identificación'}),
            'parentesco': forms.Select(attrs={'class': 'form-control'}),
            
            # ⭐ NUEVOS WIDGETS - Servicio Médico ⭐
            'servicio_medico': forms.Select(attrs={'class': 'form-control'}),
            'numero_seguro_social': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 12345678901',
                'maxlength': '20'
            }),
            
            # Información laboral
            'es_trabajador': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_es_trabajador',
                'style': 'width: 20px; height: 20px; cursor: pointer;'
            }),
            'dependencia': forms.Select(attrs={'class': 'form-control', 'id': 'id_dependencia', 'disabled': 'disabled'}),
            'departamento': forms.Select(attrs={'class': 'form-control', 'id': 'id_departamento', 'disabled': 'disabled'}),
            'estatus_laboral': forms.Select(attrs={'class': 'form-control', 'disabled': 'disabled'}),
            'numero_empleado': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de empleado', 'disabled': 'disabled'}),
            'fecha_alta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'disabled': 'disabled'}),
            'fecha_baja': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'disabled': 'disabled'}),
            
            # Notas
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones adicionales'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar departamentos según la dependencia seleccionada
        if 'dependencia' in self.data:
            try:
                dependencia_id = int(self.data.get('dependencia'))
                self.fields['departamento'].queryset = Departamento.objects.filter(
                    dependencia_id=dependencia_id, activo=True
                )
            except (ValueError, TypeError):
                self.fields['departamento'].queryset = Departamento.objects.none()
        elif self.instance.pk and self.instance.dependencia:
            self.fields['departamento'].queryset = Departamento.objects.filter(
                dependencia=self.instance.dependencia, activo=True
            )
        else:
            self.fields['departamento'].queryset = Departamento.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        es_trabajador = cleaned_data.get('es_trabajador')
        
        # Validar campos laborales si es trabajador
        if es_trabajador:
            dependencia = cleaned_data.get('dependencia')
            estatus_laboral = cleaned_data.get('estatus_laboral')
            
            if not dependencia:
                self.add_error('dependencia', 'Este campo es obligatorio para trabajadores.')
            
            if not estatus_laboral:
                self.add_error('estatus_laboral', 'Este campo es obligatorio para trabajadores.')
            
            # Si está de alta, validar fecha de alta
            if estatus_laboral == 'ALTA' and not cleaned_data.get('fecha_alta'):
                self.add_error('fecha_alta', 'Debe especificar la fecha de alta.')
            
            # Si está de baja, validar fecha de baja
            if estatus_laboral == 'BAJA' and not cleaned_data.get('fecha_baja'):
                self.add_error('fecha_baja', 'Debe especificar la fecha de baja.')
        
        return cleaned_data


class NinoForm(forms.ModelForm):
    """Formulario para registrar niños"""
    class Meta:
        model = Nino
        fields = [
            'nombre', 'apellido_paterno', 'apellido_materno',
            'fecha_nacimiento', 'tipo_sangre', 'grupo', 
            'alergias', 'medicamentos', 'foto'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_paterno': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'form-control'}),
            
            # ⭐ CORREGIDO: formato de fecha correcto
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }, format='%Y-%m-%d'),
            
            'tipo_sangre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: O+, A-'}),
            'grupo': forms.Select(attrs={'class': 'form-control'}),
            'alergias': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'medicamentos': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'foto': forms.FileInput(attrs={'class': 'form-control-file'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ⭐ Asegurar que la fecha se muestre correctamente al editar
        self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']


class AsignarTutorForm(forms.Form):
    """Formulario para asignar tutores a un niño"""
    tutores = forms.ModelMultipleChoiceField(
        queryset=Tutor.objects.filter(activo=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Tutores Autorizados"
    )


class DependenciaForm(forms.ModelForm):
    """Formulario para registrar dependencias"""
    class Meta:
        model = Dependencia
        fields = ['nombre', 'siglas', 'direccion', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'siglas': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: SEP, IMSS'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'})
        }


class DepartamentoForm(forms.ModelForm):
    """Formulario para registrar departamentos"""
    class Meta:
        model = Departamento
        fields = ['dependencia', 'nombre', 'descripcion']
        widgets = {
            'dependencia': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }


# ⭐ NUEVO FORMULARIO ⭐
class ServicioMedicoForm(forms.ModelForm):
    """Formulario para registrar servicios médicos"""
    class Meta:
        model = ServicioMedico
        fields = ['nombre', 'siglas', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Instituto Mexicano del Seguro Social'}),
            'siglas': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: IMSS'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ⭐ NUEVO FORMULARIO ⭐
class GrupoForm(forms.ModelForm):
    """Formulario para registrar grupos"""
    class Meta:
        model = Grupo
        fields = ['nombre', 'tipo', 'grado', 'capacidad_maxima']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Grupo A, Sala 1'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'grado': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1er año, 2do año'}),
            'capacidad_maxima': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '50', 'value': '20'}),
        }


# ⭐ NUEVO FORMULARIO ⭐
class ObservacionNinoForm(forms.ModelForm):
    """Formulario para registrar observaciones de niños"""
    class Meta:
        model = ObservacionNino
        fields = ['nino', 'tipo', 'descripcion', 'fecha', 'importante', 'notificar_tutor']
        widgets = {
            'nino': forms.Select(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ej: El alumno ingresó sin mandil'
            }),
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            
            # ⭐ CORREGIDO: Sin clases conflictivas
            'importante': forms.CheckboxInput(attrs={
                'class': 'custom-control-input',
                'id': 'id_importante'
            }),
            'notificar_tutor': forms.CheckboxInput(attrs={
                'class': 'custom-control-input',
                'id': 'id_notificar_tutor'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar niños activos
        self.fields['nino'].queryset = Nino.objects.filter(activo=True).order_by('apellido_paterno', 'nombre')
        # ⭐ Formato de fecha correcto
        self.fields['fecha'].input_formats = ['%Y-%m-%d']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar niños activos
        self.fields['nino'].queryset = Nino.objects.filter(activo=True).order_by('apellido_paterno', 'nombre')