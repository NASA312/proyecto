from django import forms
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class TutorForm(forms.ModelForm):
    # Campo colonia: queryset vacío, se llena via AJAX
    colonia = forms.ModelChoiceField(
        queryset=Colonia.objects.none(),  # ← CLAVE: no carga nada al inicio
        required=False,
        widget=forms.HiddenInput(),       # ← oculto, el usuario usa el autocomplete
    )

    class Meta:
        model = Tutor
        exclude = ['huella_template', 'huella_imagen', 'huella_registrada', 
                   'fecha_registro_huella', 'fecha_registro', 'fecha_modificacion','activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_paterno': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_emergencia': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'codigo_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '5',
                'placeholder': '00000',
            }),
            'calle': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_exterior': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_interior': forms.TextInput(attrs={'class': 'form-control'}),
            'referencias': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'tipo_identificacion': forms.Select(attrs={'class': 'form-control'}),
            'numero_identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'parentesco': forms.Select(attrs={'class': 'form-control'}),
            'servicio_medico': forms.Select(attrs={'class': 'form-control'}),
            'numero_seguro_social': forms.TextInput(attrs={'class': 'form-control'}),
            'es_trabajador': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'dependencia': forms.Select(attrs={'class': 'form-control'}),
            'departamento': forms.Select(attrs={'class': 'form-control'}),
            'estatus_laboral': forms.Select(attrs={'class': 'form-control'}),
            'numero_empleado': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_alta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_baja': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si viene un POST con colonia_id, incluirla en el queryset para que valide
        colonia_id = None
        if args and hasattr(args[0], 'get'):          # args[0] es el QueryDict del POST
            colonia_id = args[0].get('colonia')
        
        if colonia_id:
            # Validar solo la colonia que viene en el POST
            self.fields['colonia'].queryset = Colonia.objects.filter(pk=colonia_id)
        elif self.instance and self.instance.pk and self.instance.colonia_id:
            # Modo editar sin cambios: mantener la colonia guardada
            self.fields['colonia'].queryset = Colonia.objects.filter(
                pk=self.instance.colonia_id
            )
        else:
            self.fields['colonia'].queryset = Colonia.objects.none()
        
        self.fields['colonia'].widget = forms.HiddenInput()
        self.fields['colonia'].required = False
        
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
            'numero_matricula', 'nombre', 'apellido_paterno', 'apellido_materno',
            'fecha_nacimiento', 'genero', 'tipo_sangre', 'grupo',
            'alergias', 'medicamentos', 'foto'
        ]
        widgets = {
            'numero_matricula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: MAT-2024-001'
            }),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_paterno': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }, format='%Y-%m-%d'),
            'genero': forms.Select(attrs={'class': 'form-control'}),
            'tipo_sangre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: O+, A-'}),
            'grupo': forms.Select(attrs={'class': 'form-control'}),
            'alergias': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'medicamentos': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'foto': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_nacimiento'].input_formats = ['%Y-%m-%d']
        self.fields['numero_matricula'].required = False


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
        
class ConfiguracionGuarderiaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionGuarderia
        fields = ['tiempo_minimo_entre_registros']
        widgets = {
            'tiempo_minimo_entre_registros': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 1440,
                'placeholder': 'Ej: 30',
            })
        }
        labels = {
            'tiempo_minimo_entre_registros': 'Tiempo mínimo entre registros (minutos)',
        }
        
class ColoniaForm(forms.ModelForm):
    class Meta:
        model = Colonia
        fields = ['d_codigo', 'd_asenta', 'D_mnpio', 'd_estado']
        labels = {
            'd_codigo': 'Código Postal',
            'd_asenta': 'Nombre del Asentamiento / Colonia',
            'D_mnpio':  'Municipio',
            'd_estado': 'Estado',
        }
        widgets = {
            'd_codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. 63000',
                'maxlength': 5,
            }),
            'd_asenta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Centro',
            }),
            'D_mnpio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Tepic',
            }),
            'd_estado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Nayarit',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo al CREAR (sin instancia guardada): poner Nayarit como initial en estado
        # y vaciar los demás campos que heredan el `default` del modelo
        if not self.instance.pk:
            self.fields['d_estado'].initial = 'Nayarit'
            # Limpiar los defaults del modelo para que aparezcan como placeholder
            self.fields['d_codigo'].initial = ''
            self.fields['d_asenta'].initial = ''
            self.fields['D_mnpio'].initial = ''
        
    def clean_d_codigo(self):
        cp = self.cleaned_data.get('d_codigo', '').strip()
        if not cp.isdigit() or len(cp) != 5:
            raise forms.ValidationError("El código postal debe ser exactamente 5 dígitos.")
        return cp

    def clean_d_asenta(self):
        nombre = self.cleaned_data.get('d_asenta', '').strip()
        if len(nombre) < 2:
            raise forms.ValidationError("El nombre del asentamiento es demasiado corto.")
        return nombre.title()

    def clean_D_mnpio(self):
        return self.cleaned_data.get('D_mnpio', '').strip().title()

    def clean_d_estado(self):
        return self.cleaned_data.get('d_estado', '').strip().title()