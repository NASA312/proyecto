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

## 2. Instalar Git

Descargar desde:

https://git-scm.com/download/win

---

## 3. Instalar Python 3.13.2

Descargar desde:

https://www.python.org/downloads/release/python-3132/

Durante la instalación activar:

- ✅ Add Python to PATH
- ✅ pip
- ✅ venv

---

## 4. Clonar el repositorio

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

## 5. Crear entorno virtual

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

## 6. Instalar dependencias

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

## 7. Configurar PostgreSQL

Abrir PostgreSQL y crear la base de datos.

Ejemplo:

```sql
CREATE DATABASE proyecto;
```

También asegurarse de tener:

- Usuario: `postgres`
- Contraseña configurada

---

## 8. Crear archivo `.env`

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

## 9. Configuración de `settings.py`

Configuración importante:

```python
STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, "static-cdn", "static")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
```

---

## 10. Ejecutar migraciones

```powershell
python manage.py migrate
```

---

## 11. Cargar datos iniciales *(obligatorio)*

### 11.1 Crear roles del sistema

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

### 11.2 Cargar catálogo de colonias

```powershell
python manage.py cargar_colonias --limpiar
```

---

## 12. Crear superusuario

```powershell
python manage.py createsuperuser
```

---

## 13. Configurar archivos estáticos

Ejecutar:

```powershell
python manage.py collectstatic
```

Esto copiará los archivos estáticos a:

```text
src/static-cdn/static
```

---

## 14. Configurar Apache (XAMPP)

### 14.1 Activar módulos necesarios

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

### 14.2 Activar Virtual Hosts

Buscar:

```apache
#Include conf/extra/httpd-vhosts.conf
```

Quitar `#`:

```apache
Include conf/extra/httpd-vhosts.conf
```

---

## 15. Configuración del VirtualHost

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

## 16. Probar Django manualmente

Con el entorno virtual activado:

```powershell
waitress-serve --host=127.0.0.1 --port=8000 proyecto.wsgi:application
```

Abrir:

```text
http://127.0.0.1:8000
```

Si el sistema carga correctamente con estilos y sin errores, está listo para configurar el inicio automático.

---

## 17. Configurar inicio automático al encender Windows

Esta sección reemplaza los métodos anteriores (carpeta Startup y XAMPP Service). Se usa el **Programador de Tareas de Windows** porque:

- ✅ No requiere cuenta de administrador
- ✅ Inicia todo en segundo plano sin ventanas abiertas
- ✅ Se reinicia automáticamente si falla

---

### 17.1 Crear el script de inicio

Crear el archivo:

```text
C:\xampp\htdocs\proyecto\iniciar_sistema.bat
```

Con el siguiente contenido:

```bat
@echo off

:: 1. Iniciar Apache en segundo plano sin abrir ninguna ventana
powershell -WindowStyle Hidden -Command "Start-Process 'C:\xampp\apache\bin\httpd.exe' -WindowStyle Hidden"

:: Esperar 5 segundos para que Apache levante antes de iniciar Django
timeout /t 5 /nobreak

:: 2. Activar el entorno virtual e iniciar Django con Waitress en segundo plano
cd /d "C:\xampp\htdocs\proyecto\src"
call "C:\xampp\htdocs\proyecto\venv313\Scripts\activate.bat"
start "" /B pythonw -m waitress --host=0.0.0.0 --port=8000 proyecto.wsgi:application
```

> 💡 **¿Por qué `pythonw` en lugar de `python`?**  
> `pythonw` ejecuta Python sin abrir una ventana de consola, por lo que el servidor Django corre completamente en segundo plano.

> 💡 **¿Por qué `start "" /B`?**  
> El flag `/B` ejecuta el proceso en segundo plano sin abrir una nueva ventana.

---

### 17.2 Registrar la tarea del sistema (Apache + Django)

Abrir **PowerShell** (no requiere administrador) y ejecutar el siguiente bloque completo:

```powershell
$action = New-ScheduledTaskAction `
    -Execute "C:\xampp\htdocs\proyecto\iniciar_sistema.bat"

$trigger = New-ScheduledTaskTrigger -AtLogon -User $env:USERNAME

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
    -TaskName "IniciarSistemaGuarderia" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -RunLevel Limited `
    -Force
```

**¿Qué hace este comando?**

| Parámetro | Descripción |
|-----------|-------------|
| `-AtLogon` | La tarea se ejecuta cada vez que el usuario inicia sesión |
| `-ExecutionTimeLimit 0` | Sin límite de tiempo (el servidor corre indefinidamente) |
| `-RestartCount 3` | Si el proceso falla, intenta reiniciarlo hasta 3 veces |
| `-RunLevel Limited` | No requiere permisos de administrador |

---

### 17.3 Registrar la tarea de BiometricServerWindows

En el mismo PowerShell, ejecutar el siguiente bloque completo:

```powershell
$appref = "C:\Users\maimm\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\BiometricServerWindows\BiometricServerWindows.appref-ms"

$action2 = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c start `"`" `"$appref`""

$trigger2 = New-ScheduledTaskTrigger -AtLogon -User $env:USERNAME
$trigger2.Delay = "PT40S"

$settings2 = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 2)

Register-ScheduledTask `
    -TaskName "IniciarBiometricServer" `
    -Action $action2 `
    -Trigger $trigger2 `
    -Settings $settings2 `
    -RunLevel Limited `
    -Force
```

**¿Qué hace este comando?**

| Parámetro | Descripción |
|-----------|-------------|
| `$appref` | Ruta al acceso directo de la app biométrica (formato ClickOnce) |
| `PT40S` | Espera 40 segundos tras el login antes de iniciar (para que Windows cargue completamente) |
| `-ExecutionTimeLimit 2min` | Solo necesita 2 minutos para lanzar la app |

> 💡 **¿Por qué 40 segundos de retraso?**  
> BiometricServerWindows es una aplicación ClickOnce que necesita que el escritorio de Windows esté completamente cargado antes de poder iniciarse. Si arranca demasiado rápido puede fallar silenciosamente.

---

### 17.4 Verificar que las tareas quedaron registradas

```powershell
Get-ScheduledTask -TaskName "IniciarSistemaGuarderia"
Get-ScheduledTask -TaskName "IniciarBiometricServer"
```

Ambas deben mostrar el estado `Ready`.

---

### 17.5 Probar sin reiniciar la computadora

Para verificar que el script funciona antes de reiniciar:

```powershell
Start-ScheduledTask -TaskName "IniciarSistemaGuarderia"
```

Esperar 15 segundos y abrir:

```text
http://localhost
```

Si el sistema carga con estilos correctamente, la configuración es exitosa.

---

### 17.6 Orden de arranque al encender Windows

Al iniciar sesión, el sistema arranca en este orden:
Login de Windows
│
├── 0s → Apache (httpd.exe) inicia en segundo plano
│
├── 5s → Django/Waitress inicia en segundo plano
│
└── 40s → BiometricServerWindows inicia
---

## 18. Acceder al sistema

Abrir:

```text
http://localhost
```

---

## 19. Acceso desde otras computadoras

### Configurar `ALLOWED_HOSTS`

En `settings.py`:

```python
ALLOWED_HOSTS = ['*']
```

o especificando las IPs permitidas:

```python
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '192.168.1.50'
]
```

---

### Obtener IP local

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

## 20. Permitir Apache y Python en Firewall

Permitir en redes privadas:

- Apache HTTP Server
- Python

---

# ✅ Resultado Final

Al encender la computadora y iniciar sesión:

✅ Apache iniciará automáticamente en segundo plano  
✅ Django iniciará automáticamente en segundo plano  
✅ BiometricServerWindows iniciará automáticamente a los 40 segundos  
✅ No se abrirá ninguna ventana de consola  
✅ El sistema estará disponible en:

```text
http://localhost
```

sin ejecutar ningún comando manual.

---

# 🔧 Comandos útiles

## Activar entorno virtual

```powershell
.\venv313\Scripts\Activate.ps1
```

## Ejecutar migraciones

```powershell
python manage.py migrate
```

## Crear superusuario

```powershell
python manage.py createsuperuser
```

## Recolectar archivos estáticos

```powershell
python manage.py collectstatic
```

## Iniciar Django manualmente (con ventana, para depuración)

```powershell
cd C:\xampp\htdocs\proyecto\src
.\venv313\Scripts\Activate.ps1
waitress-serve --host=127.0.0.1 --port=8000 proyecto.wsgi:application
```

## Ver tareas programadas

```powershell
Get-ScheduledTask -TaskName "IniciarSistemaGuarderia"
Get-ScheduledTask -TaskName "IniciarBiometricServer"
```

## Eliminar tareas programadas (si necesita reconfigurar)

```powershell
Unregister-ScheduledTask -TaskName "IniciarSistemaGuarderia" -Confirm:$false
Unregister-ScheduledTask -TaskName "IniciarBiometricServer" -Confirm:$false
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
| `BiometricServer no inicia solo` | Aumentar el retraso de `PT40S` a `PT60S` en la tarea programada |
| `Django no inicia solo` | Ejecutar manualmente el bat para ver el error en consola |
| `http://localhost sin estilos` | Verificar que `collectstatic` se ejecutó y que el VirtualHost apunta a la ruta correcta |
