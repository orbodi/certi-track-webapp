@echo off
REM Script pour verifier les certificats et envoyer les alertes
REM A executer quotidiennement via le Planificateur de taches Windows

cd /d "%~dp0\.."
call venv\Scripts\activate.bat

echo [%date% %time%] Verification des certificats expirant...
python manage.py check_expirations

echo [%date% %time%] Termine




