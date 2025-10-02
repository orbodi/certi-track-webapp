#!/bin/bash

################################################################################
# Script de gestion CertiTrack
# Description : Facilite les tâches courantes de gestion
# Usage : ./manage-app.sh [commande]
################################################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

# Détecter la commande Docker Compose
if command -v docker-compose &> /dev/null; then
    DC="docker-compose"
else
    DC="docker compose"
fi

# Fonction d'aide
show_help() {
    cat << EOF
Usage: ./manage-app.sh [COMMANDE]

Commandes disponibles:

  Gestion de l'application:
    start              Démarrer l'application
    stop               Arrêter l'application
    restart            Redémarrer l'application
    status             Voir le statut des services
    logs               Voir les logs en temps réel
    logs-service NAME  Voir les logs d'un service spécifique

  Base de données:
    migrate            Appliquer les migrations
    makemigrations     Créer de nouvelles migrations
    shell-db           Accéder au shell PostgreSQL
    backup             Créer un backup de la base de données
    restore FILE       Restaurer un backup

  Django:
    shell              Ouvrir le shell Django
    createsuperuser    Créer un super utilisateur
    collectstatic      Collecter les fichiers statiques

  Celery:
    celery-status      Voir le statut de Celery
    init-schedules     Initialiser les tâches planifiées
    check-expirations  Tester les notifications (dry-run)

  Maintenance:
    clean              Nettoyer les conteneurs et volumes
    rebuild            Rebuilder les images
    update             Mettre à jour (git pull + redeploy)

Exemples:
  ./manage-app.sh start
  ./manage-app.sh logs
  ./manage-app.sh backup
  ./manage-app.sh shell

EOF
}

# Parser la commande
COMMAND="${1:-help}"

case $COMMAND in
    # Gestion de l'application
    start)
        info "Démarrage de l'application..."
        $DC up -d
        success "Application démarrée"
        $DC ps
        ;;
    
    stop)
        info "Arrêt de l'application..."
        $DC down
        success "Application arrêtée"
        ;;
    
    restart)
        info "Redémarrage de l'application..."
        $DC restart
        success "Application redémarrée"
        $DC ps
        ;;
    
    status)
        info "Statut des services:"
        echo ""
        $DC ps
        ;;
    
    logs)
        info "Logs en temps réel (Ctrl+C pour quitter)..."
        $DC logs -f --tail=100
        ;;
    
    logs-service)
        SERVICE=$2
        if [ -z "$SERVICE" ]; then
            error "Usage: ./manage-app.sh logs-service [web|celery|celery-beat|db|redis]"
            exit 1
        fi
        info "Logs du service $SERVICE (Ctrl+C pour quitter)..."
        $DC logs -f --tail=100 $SERVICE
        ;;
    
    # Base de données
    migrate)
        info "Application des migrations..."
        $DC exec web python manage.py migrate
        success "Migrations appliquées"
        ;;
    
    makemigrations)
        info "Création des migrations..."
        $DC exec web python manage.py makemigrations
        success "Migrations créées"
        ;;
    
    shell-db)
        info "Connexion au shell PostgreSQL..."
        $DC exec db psql -U postgres -d certitrack
        ;;
    
    backup)
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        info "Création du backup: $BACKUP_FILE..."
        $DC exec -T db pg_dump -U postgres certitrack > "$BACKUP_FILE"
        success "Backup créé: $BACKUP_FILE"
        ;;
    
    restore)
        BACKUP_FILE=$2
        if [ -z "$BACKUP_FILE" ]; then
            error "Usage: ./manage-app.sh restore <fichier.sql>"
            exit 1
        fi
        if [ ! -f "$BACKUP_FILE" ]; then
            error "Fichier introuvable: $BACKUP_FILE"
            exit 1
        fi
        warning "⚠️  Cette action va ÉCRASER la base de données actuelle !"
        read -p "Êtes-vous sûr ? (oui/non): " -r
        if [[ $REPLY =~ ^[Oo]ui$ ]]; then
            info "Restauration du backup..."
            $DC exec -T db psql -U postgres certitrack < "$BACKUP_FILE"
            success "Backup restauré"
        else
            info "Restauration annulée"
        fi
        ;;
    
    # Django
    shell)
        info "Ouverture du shell Django..."
        $DC exec web python manage.py shell
        ;;
    
    createsuperuser)
        info "Création d'un super utilisateur..."
        $DC exec web python manage.py createsuperuser
        ;;
    
    collectstatic)
        info "Collecte des fichiers statiques..."
        $DC exec web python manage.py collectstatic --noinput
        success "Fichiers statiques collectés"
        ;;
    
    # Celery
    celery-status)
        info "Statut de Celery:"
        echo ""
        echo "Celery Worker:"
        $DC logs celery --tail=10
        echo ""
        echo "Celery Beat:"
        $DC logs celery-beat --tail=10
        ;;
    
    init-schedules)
        info "Initialisation des tâches planifiées..."
        $DC exec web python manage.py init_celery_schedules
        success "Tâches initialisées"
        ;;
    
    check-expirations)
        info "Test des notifications (mode dry-run)..."
        $DC exec web python manage.py check_expirations --dry-run
        ;;
    
    # Maintenance
    clean)
        warning "⚠️  Cette action va supprimer tous les conteneurs, volumes et images !"
        read -p "Êtes-vous sûr ? (oui/non): " -r
        if [[ $REPLY =~ ^[Oo]ui$ ]]; then
            info "Nettoyage en cours..."
            $DC down -v --remove-orphans
            docker system prune -f
            success "Nettoyage terminé"
        else
            info "Nettoyage annulé"
        fi
        ;;
    
    rebuild)
        info "Rebuild des images..."
        $DC build --no-cache
        success "Images rebuildées"
        info "Redémarrez l'application avec: ./manage-app.sh restart"
        ;;
    
    update)
        info "Mise à jour de l'application..."
        
        # Vérifier Git
        if [ -d ".git" ]; then
            info "Git pull..."
            git pull
        else
            warning "Pas de dépôt Git détecté"
        fi
        
        # Redéployer
        info "Redéploiement..."
        ./deploy.sh --no-cache
        success "Mise à jour terminée"
        ;;
    
    # Aide
    help|--help|-h)
        show_help
        ;;
    
    *)
        error "Commande inconnue: $COMMAND"
        echo ""
        info "Utilisez './manage-app.sh help' pour voir les commandes disponibles"
        exit 1
        ;;
esac

