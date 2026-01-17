@echo off
REM Script de démarrage du serveur Django (sans warnings GLib)
call venv\Scripts\activate
python manage.py runserver 2>&1 | findstr /v "GLib-GIO-WARNING"
