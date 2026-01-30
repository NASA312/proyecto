from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Perfil, Rol
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.utils import timezone


# ============================================
# FORMULARIO DE LOGIN (YA EXISTENTE)
# ============================================

class LoginForm(forms.Form):
    """Formulario de inicio de sesión"""
    usuario = forms.CharField(
        max_length=150,
        label='Usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuario'
        })
    )
    contrasena = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-10'


# ============================================
# FORMULARIO DE REGISTRO SIMPLIFICADO
# ============================================

class RegistroUsuarioForm(UserCreationForm):
    """Formulario simplificado para registrar nuevos usuarios del sistema"""
    
    # Campos básicos de User
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        }),
        label='Correo Electrónico'
    )
    first_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre(s)'
        }),
        label='Nombre(s)'
    )
    last_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellidos'
        }),
        label='Apellidos'
    )
    
    # Campo del Perfil - Solo ROL (lo más importante)
    rol = forms.ModelChoiceField(
        queryset=Rol.objects.filter(activo=True),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Rol en el Sistema',
        help_text='Selecciona el rol que tendrá el usuario'
    )
    
    # Campos opcionales
    telefono = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(123) 456-7890'
        }),
        label='Teléfono'
    )
    
    fecha_nacimiento = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de Nacimiento'
    )
    
    direccion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Dirección completa'
        }),
        label='Dirección'
    )
    
    foto_perfil = forms.ImageField(
        required=False,
        label='Foto de Perfil',
        help_text='Imagen del usuario'
    )
    
    fecha_ingreso = forms.DateField(
        required=False,
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de Ingreso',
        help_text='Fecha en que ingresó a la institución'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario (sin espacios)'
            }),
        }
        labels = {
            'username': 'Nombre de Usuario',
            'password1': 'Contraseña',
            'password2': 'Confirmar Contraseña',
        }
        help_texts = {
            'username': 'Requerido. 150 caracteres o menos. Letras, números y @/./+/-/_ solamente.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar widgets de contraseñas
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña segura'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Repite la contraseña'
        })
        
        # 🔥 QUITAR TODAS LAS VALIDACIONES DE CONTRASEÑA
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
        
        # Crispy forms helper
        self.helper = FormHelper()
        self.helper.form_method = 'post'
    
    def clean_email(self):
        """Validar que el email no esté registrado"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado.')
        return email
    
    def _post_clean(self):
        """
        🔥 SOBREESCRIBIR VALIDACIÓN DE CONTRASEÑA
        Esto elimina las validaciones estrictas de Django
        """
        super(forms.ModelForm, self)._post_clean()
        # Validar que las contraseñas coincidan
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                self.add_error('password2', 'Las dos contraseñas no coinciden.')
    
    def clean_username(self):
        """Convertir username a minúsculas"""
        username = self.cleaned_data.get('username')
        return username.lower() if username else username
    
    def save(self, commit=True):
        """Guardar usuario y su perfil"""
        user = super().save(commit=False)
        user.username = user.username.lower()  # Asegurar minúsculas
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_staff = True  # Permitir acceso al admin de Django
        
        if commit:
            user.save()
            
            # Generar número de empleado automático
            numero_empleado = f"EMP{user.id:05d}"  # Ejemplo: EMP00001, EMP00002
            
            # Actualizar el perfil (se crea automáticamente por el signal)
            perfil = user.perfil
            perfil.rol = self.cleaned_data['rol']
            perfil.telefono = self.cleaned_data.get('telefono', '')
            perfil.fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
            perfil.direccion = self.cleaned_data.get('direccion', '')
            perfil.numero_empleado = numero_empleado
            perfil.fecha_ingreso = self.cleaned_data.get('fecha_ingreso')
            
            # Guardar foto de perfil si se subió
            if self.cleaned_data.get('foto_perfil'):
                perfil.foto_perfil = self.cleaned_data['foto_perfil']
            
            perfil.activo = True
            perfil.save()
        
        return user


class EditarUsuarioForm(forms.ModelForm):
    """Formulario para editar usuarios existentes"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label='Correo Electrónico'
    )
    
    first_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Nombre(s)'
    )
    
    last_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Apellidos'
    )
    
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'style': 'width: 20px; height: 20px; cursor: pointer;'
        }),
        label='Usuario Activo'
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'is_active'] 
        

class EditarPerfilForm(forms.ModelForm):
    """Formulario para editar el perfil del usuario"""
    
    class Meta:
        model = Perfil
        fields = ['rol', 'telefono', 'activo']  # 👈 Quitar 'fecha_ingreso' de aquí
        widgets = {
            'rol': forms.Select(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(123) 456-7890'}),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'style': 'width: 20px; height: 20px; cursor: pointer;'
            }),
        }
        labels = {
            'rol': 'Rol en el Sistema',
            'telefono': 'Teléfono',
            'activo': 'Perfil Activo',
        }