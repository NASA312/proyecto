@echo off
echo Iniciando sistema...

:: 1. Iniciar XAMPP
start "" "C:\xampp\xampp-control.exe"
timeout /t 5 /nobreak

:: 2. Iniciar Django
cd /d "C:\xampp\htdocs\proyecto\src"
call "C:\xampp\htdocs\proyecto\venv313\Scripts\activate.bat"
start "" pythonw -m waitress --host=0.0.0.0 --port=8000 proyecto.wsgi:application