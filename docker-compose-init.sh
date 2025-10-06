#!/bin/bash

# CertiTrack - Script d'initialisation automatique avec Docker Compose
# Ce script automatise toutes les étapes nécessaires au démarrage

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

# Vérification des prérequis
check_prerequisites() {
    log_info "Vérification des prérequis..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé ou n'est pas dans le PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose n'est pas installé ou n'est pas dans le PATH"
        exit 1
    fi
    
    log_success "Prérequis vérifiés"
}

# Construction des images
build_images() {
    log_info "Construction des images Docker..."
    docker-compose build --no-cache
    log_success "Images construites avec succès"
}

# Démarrage des services
start_services() {
    log_info "Démarrage des services..."
    docker-compose up -d
    log_success "Services démarrés"
}

# Attendre que les services soient prêts
wait_for_services() {
    log_info "Attente du démarrage des services..."
    
    # Attendre PostgreSQL
    log_info "Attente de PostgreSQL..."
    until docker-compose exec -T db pg_isready -U certitrack_user -d certitrack; do
        log_info "PostgreSQL n'est pas encore prêt, attente..."
        sleep 2
    done
    log_success "PostgreSQL est prêt"
    
    # Attendre Redis
    log_info "Attente de Redis..."
    until docker-compose exec -T redis redis-cli ping; do
        log_info "Redis n'est pas encore prêt, attente..."
        sleep 2
    done
    log_success "Redis est prêt"
    
    # Attendre que l'application web soit prête
    log_info "Attente de l'application web..."
    until docker-compose exec -T web python manage.py check; do
        log_info "L'application web n'est pas encore prête, attente..."
        sleep 3
    done
    log_success "Application web est prête"
}

# Installation de Bootstrap local si nécessaire
install_bootstrap() {
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
}

# Exécution des migrations
run_migrations() {
    log_info "Exécution des migrations de base de données..."
    docker-compose exec -T web python manage.py migrate
    log_success "Migrations exécutées"
}

# Collecte des fichiers statiques
collect_static() {
    log_info "Collecte des fichiers statiques..."
    docker-compose exec -T web python manage.py collectstatic --noinput
    log_success "Fichiers statiques collectés"
}

# Initialisation des tâches Celery
init_celery_tasks() {
    log_info "Initialisation des tâches Celery..."
    docker-compose exec -T web python manage.py init_celery_schedules
    log_success "Tâches Celery initialisées"
}

# Mise à jour des jours restants
update_days_remaining() {
    log_info "Mise à jour des jours restants..."
    docker-compose exec -T web python manage.py update_days_remaining
    log_success "Jours restants mis à jour"
}

# Vérification finale
final_check() {
    log_info "Vérification finale..."
    
    # Vérifier que tous les services sont en cours d'exécution
    if docker-compose ps | grep -q "Up"; then
        log_success "Tous les services sont en cours d'exécution"
    else
        log_error "Certains services ne sont pas en cours d'exécution"
        docker-compose ps
        exit 1
    fi
    
    # Vérifier que l'application répond
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ | grep -q "200\|302"; then
        log_success "L'application répond correctement"
    else
        log_warning "L'application ne répond pas encore, cela peut prendre quelques secondes"
    fi
}

# Affichage des informations de connexion
show_connection_info() {
    echo ""
    log_info "=== CertiTrack est prêt ! ==="
    echo ""
    echo -e "${GREEN}🌐 Application Web:${NC} http://localhost:8000"
    echo -e "${GREEN}📊 Dashboard Mural:${NC} http://localhost:8000/dashboard/wall/"
    echo -e "${GREEN}🔧 Admin Django:${NC} http://localhost:8000/admin/"
    echo ""
    echo -e "${BLUE}📋 Services actifs:${NC}"
    docker-compose ps
    echo ""
    echo -e "${YELLOW}💡 Commandes utiles:${NC}"
    echo "  - Arrêter: docker-compose down"
    echo "  - Logs: docker-compose logs -f"
    echo "  - Redémarrer: docker-compose restart"
    echo "  - Shell Django: docker-compose exec web python manage.py shell"
    echo ""
    echo -e "${GREEN}✅ Initialisation terminée avec succès !${NC}"
}

# Fonction principale
main() {
    echo -e "${BLUE}"
    echo "=========================================="
    echo "    CertiTrack - Initialisation Auto"
    echo "=========================================="
    echo -e "${NC}"
    
    check_prerequisites
    build_images
    start_services
    wait_for_services
    install_bootstrap
    run_migrations
    collect_static
    init_celery_tasks
    update_days_remaining
    final_check
    show_connection_info
}

# Gestion des erreurs
trap 'log_error "Une erreur est survenue. Arrêt du script."; exit 1' ERR

# Exécution du script principal
main "$@"
