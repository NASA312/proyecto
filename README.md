# 🏫 SISTEMA DE CONTROL DE ACCESO CENDI 2

## 📋 Instalación

Guía completa de instalación y configuración de Guardería Digital.

---

## ⚙️ Prerrequisitos

Antes de instalar Guardería Digital, asegúrese de tener los siguientes requisitos:

| Requisito | Descripción |
|-----------|-------------|
| **Python 3.8+** | La aplicación está construida con Django 5.1.6 |
| **PostgreSQL 12+** | Sistema de base de datos principal |
| **.NET SDK** | Necesario para el servicio de captura de huellas dactilares (`DigitalPersonaCaptureFixed`) |
| **pip** | Instalador de paquetes de Python |
| **virtualenv / venv** | Para crear entornos Python aislados |
| **Git** | Para clonar el repositorio |

> ⚠️ El servicio de huellas dactilares .NET se ejecuta en `http://localhost:5000` y debe estar disponible para que la autenticación biométrica funcione correctamente.

---

## 🚀 Pasos de instalación

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd guarderia-digital
```

### 2. Crear entorno virtual
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

> El símbolo del sistema ahora debería mostrarse `(venv)` indicando que el entorno virtual está activo.

### 3. Instalar dependencias de Python
```bash
pip install -r requirements.txt
```

Esto instalará las siguientes dependencias clave:

| Paquete | Versión | Descripción |
|---------|---------|-------------|
| `Django` | 5.1.6 | Marco web |
| `psycopg2` | 2.9.10 | Adaptador de PostgreSQL |
| `django-crispy-forms` | 2.3 | Representación de formularios |
| `crispy-bootstrap4` | 2024.10 | Integración con Bootstrap 4 |
| `python-decouple` | 3.8 | Gestión de variables de entorno |
| `dj-database-url` | 2.3.0 | Análisis de URL de bases de datos |
| `pandas` | 2.3.3 | Manipulación de datos para informes |
| `openpyxl` | 3.1.5 | Manejo de archivos de Excel |
| `XlsxWriter` | 3.2.2 | Generación de archivos de Excel |
| `Pillow` | 12.1.0 | Procesamiento de imágenes |
| `requests` | 2.32.5 | Biblioteca HTTP |

> 💡 Si tiene problemas con `psycopg2`, intente instalar la versión binaria:
> ```bash
> pip install psycopg2-binary
> ```

### 4. Configurar la base de datos PostgreSQL

Cree una base de datos PostgreSQL para la aplicación:
```sql
CREATE DATABASE proyecto;
CREATE USER postgres WITH PASSWORD 'your_password';
ALTER ROLE postgres SET client_encoding TO 'utf8';
ALTER ROLE postgres SET default_transaction_isolation TO 'read committed';
ALTER ROLE postgres SET timezone TO 'America/Mazatlan';
GRANT ALL PRIVILEGES ON DATABASE proyecto TO postgres;
```

> ⚠️ La configuración predeterminada usa el **puerto 5434**. Asegúrese de que su instancia de PostgreSQL se esté ejecutando en el puerto correcto o actualice el archivo `.env` según corresponda.

### 5. Configurar variables de entorno
```bash
cp .env.example .env
```

Edite el archivo `.env` con las credenciales y la configuración de su base de datos. Consulte la página de configuración para obtener información detallada sobre cada variable.

### 6. Ejecutar migraciones de base de datos
```bash
cd src
python manage.py migrate
```

Esto creará todas las tablas necesarias para:

- Autenticación y gestión de usuarios
- Gestión de guardería
- Registros de tutores y niños
- Servicios médicos
- Departamentos y dependencias
- Datos geográficos (colonias/barrios)

### 7. Crear una cuenta de superusuario
```bash
python manage.py createsuperuser
```

Siga las instrucciones para configurar el nombre de usuario, el correo electrónico y la contraseña.

### 8. Cargar datos iniciales *(opcional)*

Si necesita cargar datos geográficos (colonias), utilice el comando de administración personalizada:
```bash
python manage.py cargar_colonias
```

Este comando carga datos de vecindario/colonia utilizados para la validación y selección de direcciones.

### 9. Recopilar archivos estáticos
```bash
python manage.py collectstatic --noinput
```

Esto crea el directorio `static-cdn/static` con todos los activos (CSS, JavaScript, imágenes).

### 10. Configurar el servicio de huellas dactilares .NET
```bash
cd "../Servicio .NET/DigitalPersonaCaptureFixed"
dotnet restore
dotnet build
```

> ⚠️ El servicio de huellas dactilares debe estar activo en `http://localhost:5000` para poder usar las características biométricas. Asegúrese de que el **puerto 5000** esté disponible.

### 11. Iniciar el servidor de desarrollo
```bash
cd ../../src
python manage.py runserver
```

La aplicación estará disponible en **http://localhost:8000**

Para ejecutar en un puerto diferente:
```bash
python manage.py runserver 0.0.0.0:8080
```

---

## ✅ Verificar la instalación

Después de completar los pasos de instalación, verifique que todo funcione correctamente:

| Componente | URL | Descripción |
|------------|-----|-------------|
| **Aplicación Django** | http://localhost:8000 | Debería mostrar la página de inicio de sesión |
| **Panel de administración** | http://localhost:8000/admin | Inicia sesión con tus credenciales de superusuario |
| **Servicio .NET** | http://localhost:5000 | Verifica que el servicio de huellas dactilares esté activo |
| **Base de datos** | — | Comprueba que la aplicación pueda conectarse a PostgreSQL |

> Si encuentra algún problema durante la instalación, revise los registros de errores en la salida de la consola.
