@echo off
setlocal enabledelayedexpansion

REM CertiTrack - Script d'initialisation automatique avec Docker Compose (Windows)
REM Ce script automatise toutes les étapes nécessaires au démarrage

echo.
echo ==========================================
echo     CertiTrack - Initialisation Auto
echo ==========================================
echo.

REM Vérification des prérequis
echo [INFO] Vérification des prérequis...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker n'est pas installé ou n'est pas dans le PATH
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose n'est pas installé ou n'est pas dans le PATH
    exit /b 1
)

echo [SUCCESS] Prérequis vérifiés

REM Construction des images
echo [INFO] Construction des images Docker...
docker-compose build --no-cache
if errorlevel 1 (
    echo [ERROR] Erreur lors de la construction des images
    exit /b 1
)
echo [SUCCESS] Images construites avec succès

REM Démarrage des services
echo [INFO] Démarrage des services...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Erreur lors du démarrage des services
    exit /b 1
)
echo [SUCCESS] Services démarrés

REM Attendre que les services soient prêts
echo [INFO] Attente du démarrage des services...

REM Attendre PostgreSQL
echo [INFO] Attente de PostgreSQL...
:wait_postgres
docker-compose exec -T db pg_isready -U certitrack_user -d certitrack >nul 2>&1
if errorlevel 1 (
    echo [INFO] PostgreSQL n'est pas encore prêt, attente...
    timeout /t 2 /nobreak >nul
    goto wait_postgres
)
echo [SUCCESS] PostgreSQL est prêt

REM Attendre Redis
echo [INFO] Attente de Redis...
:wait_redis
docker-compose exec -T redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [INFO] Redis n'est pas encore prêt, attente...
    timeout /t 2 /nobreak >nul
    goto wait_redis
)
echo [SUCCESS] Redis est prêt

REM Attendre que l'application web soit prête
echo [INFO] Attente de l'application web...
:wait_web
docker-compose exec -T web python manage.py check >nul 2>&1
if errorlevel 1 (
    echo [INFO] L'application web n'est pas encore prête, attente...
    timeout /t 3 /nobreak >nul
    goto wait_web
)
echo [SUCCESS] Application web est prête

REM Installation de Bootstrap local si nécessaire
echo [INFO] Vérification de Bootstrap local...
if not exist "static\vendor\bootstrap\bootstrap.min.css" (
    echo [WARNING] Bootstrap non trouvé, installation en local...
    if exist "scripts\install-bootstrap-local.sh" (
        echo [INFO] Installation de Bootstrap...
        REM Note: Sur Windows, vous devrez peut-être utiliser WSL ou Git Bash pour exécuter le script .sh
        echo [WARNING] Script .sh détecté. Pour Windows, utilisez WSL ou Git Bash pour l'exécuter.
    ) else (
        echo [WARNING] Script d'installation Bootstrap non trouvé, utilisation du CDN
    )
) else (
    echo [SUCCESS] Bootstrap déjà installé localement
)

REM Exécution des migrations
echo [INFO] Exécution des migrations de base de données...
docker-compose exec -T web python manage.py migrate
if errorlevel 1 (
    echo [ERROR] Erreur lors des migrations
    exit /b 1
)
echo [SUCCESS] Migrations exécutées

REM Collecte des fichiers statiques
echo [INFO] Collecte des fichiers statiques...
docker-compose exec -T web python manage.py collectstatic --noinput
if errorlevel 1 (
    echo [ERROR] Erreur lors de la collecte des fichiers statiques
    exit /b 1
)
echo [SUCCESS] Fichiers statiques collectés

REM Initialisation des tâches Celery
echo [INFO] Initialisation des tâches Celery...
docker-compose exec -T web python manage.py init_celery_schedules
if errorlevel 1 (
    echo [ERROR] Erreur lors de l'initialisation des tâches Celery
    exit /b 1
)
echo [SUCCESS] Tâches Celery initialisées

REM Mise à jour des jours restants
echo [INFO] Mise à jour des jours restants...
docker-compose exec -T web python manage.py update_days_remaining
if errorlevel 1 (
    echo [ERROR] Erreur lors de la mise à jour des jours restants
    exit /b 1
)
echo [SUCCESS] Jours restants mis à jour

REM Vérification finale
echo [INFO] Vérification finale...
docker-compose ps

REM Affichage des informations de connexion
echo.
echo [INFO] === CertiTrack est prêt ! ===
echo.
echo 🌐 Application Web: http://localhost:8000
echo 📊 Dashboard Mural: http://localhost:8000/dashboard/wall/
echo 🔧 Admin Django: http://localhost:8000/admin/
echo.
echo 💡 Commandes utiles:
echo   - Arrêter: docker-compose down
echo   - Logs: docker-compose logs -f
echo   - Redémarrer: docker-compose restart
echo   - Shell Django: docker-compose exec web python manage.py shell
echo.
echo ✅ Initialisation terminée avec succès !
echo.

pause
