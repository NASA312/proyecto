@echo off

:: 1. Iniciar Apache SIN ventana
powershell -WindowStyle Hidden -Command "Start-Process 'C:\xampp\apache\bin\httpd.exe' -WindowStyle Hidden"
timeout /t 5 /nobreak

:: 2. Iniciar Django con waitress SIN ventana
cd /d "C:\xampp\htdocs\proyecto\src"
call "C:\xampp\htdocs\proyecto\venv313\Scripts\activate.bat"
start "" /B pythonw -m waitress --host=0.0.0.0 --port=8000 proyecto.wsgi:application