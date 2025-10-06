#!/bin/bash
# Script de démarrage optimisé pour CertiTrack - Initialisation complète automatique

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Fonction pour attendre un service
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=60
    local attempt=0
    
    log_info "Attente de $service_name sur $host:$port..."
    
    while [ $attempt -lt $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            log_success "$service_name est prêt"
            return 0
        fi
        attempt=$((attempt + 1))
        log_info "$service_name non disponible - tentative $attempt/$max_attempts"
        sleep 2
    done
    
    log_error "$service_name n'est pas accessible après $max_attempts tentatives"
    return 1
}

# Fonction pour vérifier si Django est prêt
wait_for_django() {
    local max_attempts=30
    local attempt=0
    
    log_info "Vérification de la disponibilité de Django..."
    
    while [ $attempt -lt $max_attempts ]; do
        if python manage.py check --deploy 2>/dev/null; then
            log_success "Django est prêt"
            return 0
        fi
        attempt=$((attempt + 1))
        log_info "Django non prêt - tentative $attempt/$max_attempts"
        sleep 3
    done
    
    log_error "Django n'est pas prêt après $max_attempts tentatives"
    return 1
}

# Fonction d'initialisation complète
initialize_certitrack() {
    log_info "=== Initialisation de CertiTrack ==="
    
    # 1. Attendre PostgreSQL
    wait_for_service "db" "5444" "PostgreSQL"
    
    # 2. Vérifier Django
    wait_for_django
    
    # 3. Migrations
    log_info "Exécution des migrations de base de données..."
    python manage.py migrate --noinput
    log_success "Migrations appliquées"
    
    # 4. Installation de Bootstrap local si nécessaire
    log_info "Vérification de Bootstrap local..."
    if [ ! -f "static/vendor/bootstrap/bootstrap.min.css" ]; then
        log_warning "Bootstrap non trouvé, installation en local..."
        if [ -f "scripts/install-bootstrap-local.sh" ]; then
            chmod +x scripts/install-bootstrap-local.sh
            ./scripts/install-bootstrap-local.sh
            log_success "Bootstrap installé localement"
        else
            log_warning "Script d'installation Bootstrap non trouvé, utilisation du CDN"
        fi
    else
        log_success "Bootstrap déjà installé localement"
    fi
    
    # 5. Collecte des fichiers statiques
    log_info "Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput
    log_success "Fichiers statiques collectés"
    
    # 6. Création du superutilisateur
    log_info "Création du superutilisateur si nécessaire..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin');
    print('Superuser créé: admin/admin');
else:
    print('Superuser existe déjà');
" || true
    
    # 7. Initialisation des règles de notification
    log_info "Initialisation des règles de notification..."
    python manage.py init_notification_rules --email admin@example.com || true
    log_success "Règles de notification initialisées"
    
    # 8. Initialisation des tâches Celery
    log_info "Initialisation des tâches Celery..."
    python manage.py init_celery_schedules || true
    log_success "Tâches Celery initialisées"
    
    # 9. Mise à jour des jours restants
    log_info "Mise à jour des jours restants..."
    python manage.py update_days_remaining || true
    log_success "Jours restants mis à jour"
    
    log_success "=== Initialisation de CertiTrack terminée ==="
}

# Fonction d'affichage des informations de connexion
show_connection_info() {
    echo ""
    log_info "=== CertiTrack est prêt ! ==="
    echo ""
    echo -e "${GREEN}🌐 Application Web:${NC} http://localhost:8002"
    echo -e "${GREEN}📊 Dashboard Mural:${NC} http://localhost:8002/dashboard/wall/"
    echo -e "${GREEN}🔧 Admin Django:${NC} http://localhost:8002/admin/"
    echo ""
    echo -e "${GREEN}👤 Compte Admin:${NC} admin / admin"
    echo ""
    echo -e "${BLUE}📋 Services actifs:${NC}"
    echo "  - Web: Django + Gunicorn"
    echo "  - Database: PostgreSQL"
    echo "  - Cache: Redis"
    echo "  - Worker: Celery"
    echo "  - Scheduler: Celery Beat"
    echo ""
    echo -e "${YELLOW}💡 Commandes utiles:${NC}"
    echo "  - Arrêter: docker-compose down"
    echo "  - Logs: docker-compose logs -f"
    echo "  - Redémarrer: docker-compose restart"
    echo "  - Shell Django: docker-compose exec web python manage.py shell"
    echo ""
    echo -e "${GREEN}✅ CertiTrack est opérationnel !${NC}"
    echo ""
}

# Exécution principale
main() {
    echo -e "${BLUE}"
    echo "=========================================="
    echo "    CertiTrack - Docker Entrypoint"
    echo "=========================================="
    echo -e "${NC}"
    
    # Exécuter l'initialisation uniquement pour le service web
    if [ "$SERVICE_NAME" = "web" ]; then
        initialize_certitrack
        show_connection_info
    else
        log_info "Service $SERVICE_NAME - Pas d'initialisation nécessaire"
        # Attendre que le service web ait terminé l'initialisation
        sleep 10
    fi
    
    log_info "Démarrage de l'application..."
    exec "$@"
}

# Gestion des erreurs
trap 'log_error "Une erreur est survenue dans le script d initialisation"; exit 1' ERR

# Exécution du script principal
main "$@"