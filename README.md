# 🏫 SISTEMA DE CONTROL DE ACCESO CENDI 2

## 📋 Instalación

Guía completa de instalación y configuración del sistema en WSL (Ubuntu) con Apache y PostgreSQL.

---

## ⚙️ Prerrequisitos

Antes de instalar el sistema, asegúrese de tener los siguientes requisitos:

| Requisito | Descripción |
|-----------|-------------|
| **Windows 10+** | Con WSL2 habilitado |
| **Ubuntu en WSL** | Ubuntu 22.04 o 24.04 (disponible en Microsoft Store) |
| **Python 3.13** | Versión requerida (3.14+ genera conflictos con mod_wsgi) |
| **PostgreSQL 12+** | Sistema de base de datos principal (instalado dentro de Ubuntu) |
| **Apache 2** | Servidor web con mod_wsgi |
| **Git** | Para clonar el repositorio |
| **BiometricServer.exe** | Servidor .NET de huellas, debe correr en Windows como Administrador en el puerto 5000 |

> ⚠️ El servicio de huellas dactilares .NET se ejecuta en Windows en el puerto 5000. Django lo detecta automáticamente desde WSL sin necesidad de configurar la IP manualmente.

---

## 🚀 Pasos de Instalación

### 1. Instalar dependencias en Ubuntu (WSL)

Abrir la terminal de Ubuntu y ejecutar:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install apache2 apache2-dev build-essential -y
sudo apt install postgresql postgresql-contrib libpq-dev -y
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-dev -y
```

### 2. Clonar el repositorio

```bash
cd /var/www
sudo git clone https://github.com/NASA312/proyecto.git
sudo chown -R $USER:$USER /var/www/proyecto
```

### 3. Crear entorno virtual con Python 3.13

```bash
cd /var/www/proyecto
python3.13 -m venv venv313
source venv313/bin/activate
python --version  # Debe mostrar Python 3.13.x
```

### 4. Instalar dependencias del proyecto

El archivo `requirements.txt` tiene encoding UTF-16, hay que convertirlo primero:

```bash
iconv -f UTF-16LE -t UTF-8 /var/www/proyecto/requirements.txt -o /var/www/proyecto/requirements_utf8.txt

pip install django
pip install psycopg2-binary
pip install mod_wsgi
pip install -r /var/www/proyecto/requirements_utf8.txt
```

> 💡 Se usa `psycopg2-binary` en lugar de `psycopg2` para evitar errores de compilación en el entorno de Apache/mod_wsgi.

Dependencias principales que se instalan:

| Paquete | Versión | Descripción |
|---------|---------|-------------|
| `Django` | 5.1.6 | Framework web |
| `psycopg2-binary` | 2.9.10 | Adaptador de PostgreSQL |
| `django-crispy-forms` | 2.3 | Renderizado de formularios |
| `crispy-bootstrap4` | 2024.10 | Integración con Bootstrap 4 |
| `python-decouple` | 3.8 | Gestión de variables de entorno |
| `dj-database-url` | 2.3.0 | Parseo de URL de base de datos |
| `pandas` | 2.3.3 | Manipulación de datos para reportes |
| `openpyxl` | 3.1.5 | Manejo de archivos Excel |
| `XlsxWriter` | 3.2.2 | Generación de archivos Excel |
| `Pillow` | 12.1.0 | Procesamiento de imágenes |
| `requests` | 2.32.5 | Librería HTTP |

### 5. Configurar PostgreSQL

```bash
sudo service postgresql start
sudo -u postgres psql
```

Dentro del prompt de PostgreSQL ejecutar:

```sql
ALTER USER postgres WITH PASSWORD 'Marez356';
CREATE DATABASE proyecto;
GRANT ALL PRIVILEGES ON DATABASE proyecto TO postgres;
ALTER DATABASE proyecto OWNER TO postgres;
\q
```

### 6. Crear el archivo `.env`

El archivo `.env` debe crearse dentro de la carpeta `src/`, junto al `manage.py`:

```bash
nano /var/www/proyecto/src/.env
```

Contenido:

```env
SECRET_KEY=ProyectoHuellaDigital
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL_DEFAULT=postgresql://postgres:Marez356@localhost:5432/proyecto
BIOMETRIC_SERVER_URL=http://auto:5000
```

> ⚠️ `BIOMETRIC_SERVER_URL` usa `auto` como host. Django detecta automáticamente la IP de Windows desde WSL. El puerto `5000` corresponde al `BiometricServer.exe` que debe estar corriendo en Windows.

### 7. Configurar `settings.py`

Agregar al archivo `src/proyecto/settings.py` la lógica de detección automática de la IP de Windows:

```python
import subprocess
from decouple import config

def get_biometric_url():
    _url_env = config('BIOMETRIC_SERVER_URL', default='http://localhost:5000')
    _port = _url_env.split(':')[-1]

    es_wsl = False
    try:
        with open('/proc/version', 'r') as f:
            if 'microsoft' in f.read().lower():
                es_wsl = True
    except Exception:
        pass

    if es_wsl:
        try:
            result = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split()
                if 'via' in parts:
                    windows_ip = parts[parts.index('via') + 1]
                    return f'http://{windows_ip}:{_port}'
        except Exception:
            pass

    return f'http://localhost:{_port}'

BIOMETRIC_SERVER_URL = get_biometric_url()

CORS_ALLOWED_ORIGINS = [BIOMETRIC_SERVER_URL]
CSRF_TRUSTED_ORIGINS = [BIOMETRIC_SERVER_URL]
```

Todas las vistas que se conecten al servidor biométrico deben usar:

```python
from django.conf import settings

# En lugar de: requests.get('http://localhost:5000/capturar')
# Usar:
requests.get(f'{settings.BIOMETRIC_SERVER_URL}/capturar?persona_id={id}')
```

### 8. Ejecutar migraciones

```bash
cd /var/www/proyecto/src
source ../venv313/bin/activate
python manage.py migrate
```

### 9. Cargar datos iniciales *(obligatorio)*

> ⚠️ Sin estos datos el sistema no funcionará correctamente. Los roles son necesarios para el login y las colonias para el registro de direcciones.

**9.1 Crear los roles del sistema**

```bash
python manage.py shell
```

Dentro del shell de Django:

```python
from login.models import Rol
[Rol.objects.get_or_create(nombre=r) for r in ['ADMIN', 'OBSERVADOR', 'EMPLEADO']]
exit()
```

**9.2 Cargar el catálogo de colonias**

```bash
python manage.py cargar_colonias --limpiar
```

### 10. Crear superusuario y recolectar estáticos

```bash
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 11. Configurar `wsgi.py`

Editar `src/proyecto/wsgi.py`:

```python
import os
import sys

path = '/var/www/proyecto/src'
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 12. Configurar Apache

**Obtener la ruta del módulo mod_wsgi** (con el venv activado):

```bash
source /var/www/proyecto/venv313/bin/activate
mod_wsgi-express module-config
```

Copiar las dos líneas que genera y agregarlas al **final** de `/etc/apache2/apache2.conf`:

```bash
sudo nano /etc/apache2/apache2.conf
```

```apache
LoadModule wsgi_module "/var/www/proyecto/venv313/lib/python3.13/site-packages/mod_wsgi/server/mod_wsgi-py313.cpython-313-x86_64-linux-gnu.so"
WSGIPythonHome "/var/www/proyecto/venv313"
```

Crear el archivo de configuración del sitio:

```bash
sudo nano /etc/apache2/sites-available/proyecto.conf
```

```apache
<VirtualHost *:80>
    ServerName localhost

    Alias /static/ /var/www/proyecto/src/static-cdn/static/
    <Directory /var/www/proyecto/src/static-cdn/static>
        Require all granted
    </Directory>

    Alias /media/ /var/www/proyecto/src/static-cdn/media/
    <Directory /var/www/proyecto/src/static-cdn/media>
        Require all granted
    </Directory>

    WSGIDaemonProcess proyecto \
        python-home=/var/www/proyecto/venv313 \
        python-path=/var/www/proyecto/src

    WSGIProcessGroup proyecto
    WSGIApplicationGroup %{GLOBAL}

    WSGIScriptAlias / /var/www/proyecto/src/proyecto/wsgi.py

    <Directory /var/www/proyecto/src/proyecto>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/proyecto_error.log
    CustomLog ${APACHE_LOG_DIR}/proyecto_access.log combined
</VirtualHost>
```

### 13. Activar el sitio y reiniciar Apache

```bash
sudo a2dissite 000-default.conf
sudo a2ensite proyecto.conf
sudo chown -R www-data:www-data /var/www/proyecto/src/static-cdn
sudo chmod -R 755 /var/www/proyecto
sudo service apache2 restart
```

---

## ✅ Verificar la instalación

| Componente | URL | Descripción |
|------------|-----|-------------|
| **Aplicación Django** | http://localhost | Debe mostrar la página de inicio de sesión |
| **Panel de administración** | http://localhost/admin | Inicia sesión con las credenciales del superusuario |
| **Servidor biométrico** | http://localhost:5000/test | Verifica que el BiometricServer.exe esté activo en Windows |
| **Base de datos** | — | Si la app carga, la conexión a PostgreSQL es correcta |

---

## 🔧 Mantenimiento

Los servicios de WSL **no persisten** entre sesiones. Cada vez que abras Ubuntu ejecutar:

```bash
sudo service postgresql start
sudo service apache2 start
```

Ver logs de errores en tiempo real:

```bash
sudo tail -f /var/log/apache2/proyecto_error.log
```

Probar Django sin Apache (para diagnosticar errores):

```bash
cd /var/www/proyecto/src
source ../venv313/bin/activate
python manage.py runserver
# Abrir: http://127.0.0.1:8000
```

---

## 🐛 Errores Comunes

| Error | Solución |
|-------|----------|
| `No module named django` | `pip install django` (con venv313 activado) |
| `Error loading psycopg2` | `pip install psycopg2-binary` |
| `populate() isn't reentrant` | Agregar `WSGIApplicationGroup %{GLOBAL}` en `proyecto.conf` |
| `No module named proyecto` | Agregar `sys.path.append('/var/www/proyecto/src')` en `wsgi.py` |
| `Servidor .NET no disponible` | Verificar que `BiometricServer.exe` corre en Windows como Administrador |
| `Internal Server Error` | Revisar: `sudo tail -50 /var/log/apache2/proyecto_error.log` |
| No hay roles al crear usuario | Ejecutar el comando de creación de roles (Paso 9.1) |
| Error en campo colonia | Ejecutar: `python manage.py cargar_colonias --limpiar` (Paso 9.2) |
