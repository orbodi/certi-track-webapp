@echo off
REM Script pour envoyer le resume quotidien
REM A executer quotidiennement via le Planificateur de taches Windows

cd /d "%~dp0\.."
call venv\Scripts\activate.bat

echo [%date% %time%] Envoi du resume quotidien...
python manage.py send_daily_summary

echo [%date% %time%] Termine






