@echo off
REM Script pour scanner automatiquement les certificats
REM A executer hebdomadairement via le Planificateur de taches Windows

cd /d "%~dp0\.."
call venv\Scripts\activate.bat

echo [%date% %time%] Scan automatique des certificats...
python manage.py shell -c "from certificates.models import Certificate; from certificates.utils import CertificateScanner; scanner = CertificateScanner(); [cert.update() for cert in Certificate.objects.filter(needs_enrichment=True)[:20]]"

echo [%date% %time%] Termine






