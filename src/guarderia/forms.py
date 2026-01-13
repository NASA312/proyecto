from django import forms
from .models import Tutor, Nino, RegistroAcceso
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class TutorForm(forms.ModelForm):
    """Formulario para registrar tutores/padres"""
    class Meta:
        model = Tutor
        fields = [
            'nombre', 'apellido_paterno', 'apellido_materno',
            'telefono', 'telefono_emergencia', 'email', 'direccion',
            'tipo_identificacion', 'numero_identificacion',
            'parentesco', 'notas'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre(s)'}),
            'apellido_paterno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido Paterno'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido Materno'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(123) 456-7890'}),
            'telefono_emergencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono de emergencia'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo_identificacion': forms.Select(attrs={'class': 'form-control'}),
            'numero_identificacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de identificación'}),
            'parentesco': forms.Select(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones adicionales'}),
        }


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
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo_sangre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: O+, A-'}),
            'grupo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Grupo A, Maternal'}),
            'alergias': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'medicamentos': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'foto': forms.FileInput(attrs={'class': 'form-control-file'}),
        }


class AsignarTutorForm(forms.Form):
    """Formulario para asignar tutores a un niño"""
    tutores = forms.ModelMultipleChoiceField(
        queryset=Tutor.objects.filter(activo=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Tutores Autorizados"
    )