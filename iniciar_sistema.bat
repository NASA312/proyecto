@echo off

:: 1. Iniciar Apache en segundo plano sin abrir ninguna ventana
powershell -WindowStyle Hidden -Command "Start-Process 'C:\xampp\apache\bin\httpd.exe' -WindowStyle Hidden"

:: Esperar 5 segundos para que Apache levante antes de iniciar Django
timeout /t 5 /nobreak

:: 2. Activar el entorno virtual e iniciar Django con Waitress en segundo plano
cd /d "C:\xampp\htdocs\proyecto\src"
call "C:\xampp\htdocs\proyecto\venv313\Scripts\activate.bat"
start "" /B pythonw -m waitress --host=0.0.0.0 --port=8000 proyecto.wsgi:application