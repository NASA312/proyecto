# 🏫 SISTEMA DE CONTROL DE ACCESO CENDI 2

## 📋 Instalación

Guía completa de instalación y configuración del sistema en **Windows** usando:

- Apache de XAMPP
- Python 3.13.2
- PostgreSQL
- Django + Waitress

---

# ⚙️ Prerrequisitos

Antes de instalar el sistema, asegúrese de tener los siguientes requisitos:

| Requisito | Descripción |
|-----------|-------------|
| **Windows 10/11** | Sistema operativo |
| **XAMPP** | Apache para Windows |
| **Python 3.13.2** | Versión requerida |
| **PostgreSQL 12+** | Sistema de base de datos |
| **Git** | Para clonar el repositorio |
| **BiometricServer.exe** | Servidor .NET de huellas, debe ejecutarse como Administrador en el puerto 5000 |

---

# 🚀 Pasos de Instalación

## 1. Instalar XAMPP

Descargar desde:

https://www.apachefriends.org/es/index.html

Instalar en:

```text
C:\xampp
```

---

# 2. Instalar Git

Descargar desde:

https://git-scm.com/download/win

---

# 3. Instalar Python 3.13.2

Descargar desde:

https://www.python.org/downloads/release/python-3132/

Durante la instalación activar:

- ✅ Add Python to PATH
- ✅ pip
- ✅ venv

---

# 4. Clonar el repositorio

Abrir PowerShell:

```powershell
cd C:\xampp\htdocs
```

Clonar proyecto:

```powershell
git clone https://github.com/NASA312/proyecto.git
```

Entrar al proyecto:

```powershell
cd proyecto\src
```

---

# 5. Crear entorno virtual

Si existen varias versiones de Python instaladas, usar la ruta exacta de Python 3.13.2:

```powershell
& "C:\Users\USUARIO\Documents\python310\python.exe" -m venv venv313
```

Activar entorno virtual:

```powershell
.\venv313\Scripts\Activate.ps1
```

Verificar versión:

```powershell
python --version
```

Debe mostrar:

```text
Python 3.13.2
```

---

# 6. Instalar dependencias

Instalar dependencias del proyecto:

```powershell
pip install -r requirements.txt
```

Instalar dependencias importantes:

```powershell
pip install psycopg2-binary
pip install waitress
```

> 💡 Se usa `psycopg2-binary` para evitar errores de compilación de PostgreSQL en Windows.

---

# 7. Configurar PostgreSQL

Abrir PostgreSQL y crear la base de datos.

Ejemplo:

```sql
CREATE DATABASE proyecto;
```

También asegurarse de tener:

- Usuario: `postgres`
- Contraseña configurada

---

# 8. Crear archivo `.env`

Crear archivo:

```text
src\.env
```

Contenido:

```env
SECRET_KEY=ProyectoHuellaDigital
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL_DEFAULT=postgresql://postgres:TU_PASSWORD@localhost:5432/proyecto
BIOMETRIC_SERVER_URL=http://localhost:5000
```

---

# 9. Configuración de `settings.py`

Configuración importante:

```python
STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, "static-cdn", "static")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
```

---

# 10. Ejecutar migraciones

```powershell
python manage.py migrate
```

---

# 11. Cargar datos iniciales *(obligatorio)*

## 11.1 Crear roles del sistema

```powershell
python manage.py shell
```

Dentro del shell:

```python
from login.models import Rol
[Rol.objects.get_or_create(nombre=r) for r in ['ADMIN', 'OBSERVADOR', 'EMPLEADO']]
exit()
```

---

## 11.2 Cargar catálogo de colonias

```powershell
python manage.py cargar_colonias --limpiar
```

---

# 12. Crear superusuario

```powershell
python manage.py createsuperuser
```

---

# 13. Configurar archivos estáticos

Ejecutar:

```powershell
python manage.py collectstatic
```

Esto copiará los archivos estáticos a:

```text
src/static-cdn/static
```

---

# 14. Configurar Apache (XAMPP)

## 14.1 Activar módulos necesarios

Abrir:

```text
C:\xampp\apache\conf\httpd.conf
```

Buscar y descomentar:

```apache
LoadModule proxy_module modules/mod_proxy.so
LoadModule proxy_http_module modules/mod_proxy_http.so
LoadModule alias_module modules/mod_alias.so
```

---

## 14.2 Activar Virtual Hosts

Buscar:

```apache
#Include conf/extra/httpd-vhosts.conf
```

Quitar `#`:

```apache
Include conf/extra/httpd-vhosts.conf
```

---

# 15. Configuración del VirtualHost

Abrir:

```text
C:\xampp\apache\conf\extra\httpd-vhosts.conf
```

Agregar:

```apache
<VirtualHost *:80>
    ServerName localhost

    ProxyPreserveHost On

    # =========================
    # STATIC FILES
    # =========================
    ProxyPass /static/ !

    Alias /static/ "C:/xampp/htdocs/proyecto/src/static-cdn/static/"

    <Directory "C:/xampp/htdocs/proyecto/src/static-cdn/static/">
        Require all granted
    </Directory>

    # =========================
    # MEDIA FILES
    # =========================
    ProxyPass /media/ !

    Alias /media/ "C:/xampp/htdocs/proyecto/src/static-cdn/media/"

    <Directory "C:/xampp/htdocs/proyecto/src/static-cdn/media/">
        Require all granted
    </Directory>

    # =========================
    # DJANGO
    # =========================
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    ErrorLog "logs/django_error.log"
    CustomLog "logs/django_access.log" common
</VirtualHost>
```

---

# 16. Probar Django manualmente

Con el entorno virtual activado:

```powershell
waitress-serve --host=127.0.0.1 --port=8000 proyecto.wsgi:application
```

Abrir:

```text
http://127.0.0.1:8000
```

---

# 17. Crear script automático de Django

Crear archivo:

```text
C:\xampp\htdocs\proyecto\src\iniciar_django.bat
```

Contenido:

```bat
@echo off

cd /d C:\xampp\htdocs\proyecto\src

call venv313\Scripts\activate

waitress-serve --host=127.0.0.1 --port=8000 proyecto.wsgi:application
```

---

# 18. Iniciar Apache

Abrir XAMPP y encender:

- Apache

---

# 19. Acceder al sistema

Abrir:

```text
http://localhost
```

---

# 20. Acceso desde otras computadoras

## Configurar `ALLOWED_HOSTS`

En `settings.py`:

```python
ALLOWED_HOSTS = ['*']
```

o:

```python
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '192.168.1.50'
]
```

---

## Obtener IP local

Ejecutar:

```powershell
ipconfig
```

Buscar:

```text
IPv4 Address
```

Ejemplo:

```text
192.168.1.50
```

Abrir desde otra computadora:

```text
http://192.168.1.50
```

---

# 21. Permitir Apache y Python en Firewall

Permitir:

- Apache HTTP Server
- Python

en redes privadas.

---

# 22. Inicio automático al encender Windows

## Apache automático

Abrir XAMPP como administrador.

En Apache marcar:

```text
Service
```

Esto hará que Apache inicie automáticamente con Windows.

---

## Django automático

Presionar:

```text
Windows + R
```

Escribir:

```text
shell:startup
```

Crear acceso directo de:

```text
C:\xampp\htdocs\proyecto\src\iniciar_django.bat
```

dentro de la carpeta Startup.

---

# ✅ Resultado Final

Al encender la computadora:

✅ Apache iniciará automáticamente  
✅ Django iniciará automáticamente  
✅ El sistema estará disponible en:

```text
http://localhost
```

sin ejecutar comandos manuales.

---

# 🔧 Comandos útiles

## Activar entorno virtual

```powershell
.\venv313\Scripts\Activate.ps1
```

---

## Ejecutar migraciones

```powershell
python manage.py migrate
```

---

## Crear superusuario

```powershell
python manage.py createsuperuser
```

---

## Recolectar archivos estáticos

```powershell
python manage.py collectstatic
```

---

# 🐛 Errores comunes

| Error | Solución |
|-------|----------|
| `No module named django` | `pip install django` |
| `Error loading psycopg2` | `pip install psycopg2-binary` |
| `Service Unavailable` | Verificar que Waitress esté ejecutándose |
| `No se muestran imágenes/CSS` | Ejecutar `python manage.py collectstatic` |
| `Internal Server Error` | Revisar `C:\xampp\apache\logs\error.log` |
| `No hay roles al crear usuarios` | Ejecutar creación de roles |
| `Error en colonias` | Ejecutar `python manage.py cargar_colonias --limpiar` |
