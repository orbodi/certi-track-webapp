#!/bin/bash

################################################################################
# Script de déploiement CertiTrack
# Description : Déploie l'application avec Docker Compose et initialise tout
# Usage : ./deploy.sh [options]
# Options:
#   --no-build       : Skip le rebuild des images Docker
#   --no-cache       : Force un rebuild complet sans cache
#   --production     : Mode production (désactive DEBUG)
#   --quick          : Déploiement rapide (sans rebuild ni collectstatic)
#   --help           : Affiche l'aide
################################################################################

set -e  # Arrêter en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/deploy.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Fonction pour afficher les messages
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
    echo "[${TIMESTAMP}] INFO: $1" >> "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
    echo "[${TIMESTAMP}] SUCCESS: $1" >> "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    echo "[${TIMESTAMP}] WARNING: $1" >> "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    echo "[${TIMESTAMP}] ERROR: $1" >> "$LOG_FILE"
}

# Fonction pour afficher l'aide
show_help() {
    cat << EOF
Usage: ./deploy.sh [OPTIONS]

Options:
  --no-build       Ne pas rebuilder les images Docker (plus rapide)
  --no-cache       Rebuilder sans cache Docker (complet)
  --production     Déployer en mode production
  --quick          Déploiement rapide (dev uniquement)
  --help           Afficher cette aide

Exemples:
  ./deploy.sh                    # Déploiement standard
  ./deploy.sh --no-build         # Sans rebuild (rapide)
  ./deploy.sh --production       # Production
  ./deploy.sh --quick            # Très rapide (dev)

EOF
    exit 0
}

# Bannière
clear
echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ██████╗███████╗██████╗ ████████╗██╗████████╗██████╗  █████╗ ║
║  ██╔════╝██╔════╝██╔══██╗╚══██╔══╝██║╚══██╔══╝██╔══██╗██╔══██╗║
║  ██║     █████╗  ██████╔╝   ██║   ██║   ██║   ██████╔╝███████║║
║  ██║     ██╔══╝  ██╔══██╗   ██║   ██║   ██║   ██╔══██╗██╔══██║║
║  ╚██████╗███████╗██║  ██║   ██║   ██║   ██║   ██║  ██║██║  ██║║
║   ╚═════╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝║
║                                                               ║
║              Gestion des Certificats SSL/TLS                 ║
║                 Powered by Atos Meda TOGO                    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Parser les arguments
BUILD=true
USE_CACHE=true
PRODUCTION=false
QUICK=false

for arg in "$@"; do
    case $arg in
        --no-build)
            BUILD=false
            shift
            ;;
        --no-cache)
            USE_CACHE=false
            shift
            ;;
        --production)
            PRODUCTION=true
            shift
            ;;
        --quick)
            QUICK=true
            BUILD=false
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            warning "Option inconnue: $arg (utilisez --help pour l'aide)"
            ;;
    esac
done

# Initialiser le fichier de log
echo "=== Déploiement CertiTrack - ${TIMESTAMP} ===" > "$LOG_FILE"

info "Démarrage du déploiement de CertiTrack..."
if [ "$PRODUCTION" = true ]; then
    warning "Mode PRODUCTION activé"
fi
if [ "$QUICK" = true ]; then
    warning "Mode QUICK activé (développement uniquement)"
fi
echo ""

# Étape 0 : Vérifier les permissions
if [ ! -w "$SCRIPT_DIR" ]; then
    error "Permissions insuffisantes dans le répertoire $SCRIPT_DIR"
    exit 1
fi

# Étape 1 : Vérifier Docker
info "Étape 1/10 : Vérification de Docker..."

if ! command -v docker &> /dev/null; then
    error "Docker n'est pas installé !"
    echo ""
    info "Pour installer Docker, exécutez : sudo ./install-prereqs.sh"
    exit 1
fi

# Vérifier que Docker est en cours d'exécution
if ! docker info &> /dev/null; then
    error "Docker n'est pas en cours d'exécution ou vous n'avez pas les permissions"
    echo ""
    info "Solutions:"
    echo "  1. Démarrer Docker : sudo systemctl start docker"
    echo "  2. Ajouter votre utilisateur au groupe docker : sudo usermod -aG docker \$USER"
    echo "  3. Puis déconnectez-vous et reconnectez-vous"
    exit 1
fi

# Vérifier Docker Compose
if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
    error "Docker Compose n'est pas installé !"
    echo ""
    info "Pour installer Docker Compose, exécutez : sudo ./install-prereqs.sh"
    exit 1
fi

# Définir la commande Docker Compose à utiliser
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

success "Docker $(docker --version | cut -d' ' -f3 | cut -d',' -f1) détecté"
success "Docker Compose détecté"
echo ""

# Étape 2 : Vérifier les fichiers requis
info "Étape 2/10 : Vérification des fichiers requis..."

if [ ! -f "docker-compose.yml" ]; then
    error "Fichier docker-compose.yml introuvable"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    error "Fichier requirements.txt introuvable"
    exit 1
fi

if [ ! -f "manage.py" ]; then
    error "Fichier manage.py introuvable"
    exit 1
fi

success "Tous les fichiers requis sont présents"
echo ""

# Étape 3 : Arrêter les conteneurs existants
info "Étape 3/10 : Arrêt des conteneurs existants..."
$DOCKER_COMPOSE down --remove-orphans >> "$LOG_FILE" 2>&1
success "Conteneurs arrêtés"
echo ""

# Étape 4 : Build des images (optionnel)
if [ "$BUILD" = true ]; then
    info "Étape 4/10 : Construction des images Docker..."
    
    if [ "$USE_CACHE" = false ]; then
        warning "Construction sans cache (peut prendre 5-10 minutes)..."
        $DOCKER_COMPOSE build --no-cache 2>&1 | tee -a "$LOG_FILE"
    else
        info "Construction avec cache..."
        $DOCKER_COMPOSE build 2>&1 | tee -a "$LOG_FILE"
    fi
    
    success "Images construites avec succès"
else
    info "Étape 4/10 : Construction des images ignorée (--no-build ou --quick)"
fi
echo ""

# Étape 5 : Démarrer les services
info "Étape 5/10 : Démarrage des conteneurs..."
$DOCKER_COMPOSE up -d >> "$LOG_FILE" 2>&1
success "Conteneurs démarrés"
echo ""

# Étape 6 : Attendre que PostgreSQL soit prêt
info "Étape 6/10 : Attente de la base de données PostgreSQL..."
MAX_RETRIES=60
RETRY_COUNT=0

while ! $DOCKER_COMPOSE exec -T db pg_isready -U postgres > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -gt $MAX_RETRIES ]; then
        error "La base de données n'a pas démarré dans les temps (${MAX_RETRIES}s)"
        echo ""
        info "Logs de la base de données:"
        $DOCKER_COMPOSE logs db
        exit 1
    fi
    echo -n "."
    sleep 1
done

echo ""
success "Base de données prête"
echo ""

# Étape 7 : Exécuter les migrations
info "Étape 7/10 : Application des migrations de la base de données..."
$DOCKER_COMPOSE exec -T web python manage.py migrate --noinput 2>&1 | tee -a "$LOG_FILE"
success "Migrations appliquées"
echo ""

# Étape 7.5 : Installer Bootstrap en local si nécessaire
info "Étape 7.5/10 : Vérification de Bootstrap local..."
if [ ! -f "static/vendor/bootstrap/bootstrap.min.css" ]; then
    warning "Bootstrap non trouvé, installation en local..."
    chmod +x scripts/install-bootstrap-local.sh
    ./scripts/install-bootstrap-local.sh >> "$LOG_FILE" 2>&1
    success "Bootstrap installé localement"
else
    success "Bootstrap déjà installé localement"
fi
echo ""

# Étape 8 : Collecter les fichiers statiques (sauf en mode quick)
if [ "$QUICK" = false ]; then
    info "Étape 8/10 : Collecte des fichiers statiques..."
    $DOCKER_COMPOSE exec -T web python manage.py collectstatic --noinput --clear >> "$LOG_FILE" 2>&1
    success "Fichiers statiques collectés"
else
    info "Étape 8/10 : Collecte des fichiers statiques ignorée (--quick)"
fi
echo ""

# Étape 9 : Initialiser les tâches Celery
info "Étape 9/10 : Initialisation des tâches planifiées Celery..."
$DOCKER_COMPOSE exec -T web python manage.py init_celery_schedules 2>&1 | tee -a "$LOG_FILE"
success "Tâches Celery initialisées"
echo ""

# Afficher l'état des services
info "État des services :"
echo ""
$DOCKER_COMPOSE ps
echo ""

# Vérifier que tous les services sont en cours d'exécution
SERVICES_DOWN=$($DOCKER_COMPOSE ps | grep -c "Exit" || true)
if [ "$SERVICES_DOWN" -gt 0 ]; then
    warning "Certains services ne sont pas en cours d'exécution"
    echo ""
    info "Vérifiez les logs : $DOCKER_COMPOSE logs"
fi

# Résumé final
echo ""
echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║                  ✅ DÉPLOIEMENT RÉUSSI ! ✅                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Récupérer l'IP du serveur
SERVER_IP=$(hostname -I | awk '{print $1}')

success "Application disponible sur :"
echo "  • Local    : http://localhost:8000"
echo "  • Réseau   : http://${SERVER_IP}:8000"
echo ""
success "Interfaces d'administration :"
echo "  • Admin Django       : http://localhost:8000/admin"
echo "  • Config horaires    : http://localhost:8000/notifications/schedules/"
echo "  • Règles notifs      : http://localhost:8000/notifications/rules/"
echo "  • Journal des logs   : http://localhost:8000/notifications/logs/"
echo ""

info "📊 Commandes utiles :"
echo "  • Voir les logs           : $DOCKER_COMPOSE logs -f"
echo "  • Arrêter                 : $DOCKER_COMPOSE down"
echo "  • Redémarrer              : $DOCKER_COMPOSE restart"
echo "  • Statut des services     : $DOCKER_COMPOSE ps"
echo "  • Voir les logs détaillés : cat $LOG_FILE"
echo ""

info "🔧 Commandes Django :"
echo "  • Créer un super utilisateur : $DOCKER_COMPOSE exec web python manage.py createsuperuser"
echo "  • Tester les notifications   : $DOCKER_COMPOSE exec web python manage.py check_expirations --dry-run"
echo "  • Shell Django               : $DOCKER_COMPOSE exec web python manage.py shell"
echo ""

info "📝 Fichiers importants :"
echo "  • Logs du déploiement    : $LOG_FILE"
echo "  • Configuration Docker   : docker-compose.yml"
echo "  • Documentation          : DEPLOYMENT.md"
echo ""

if [ "$PRODUCTION" = false ]; then
    warning "⚠️  Mode développement actif (DEBUG=True)"
    echo ""
    info "Pour le mode production, utilisez : ./deploy.sh --production"
fi

success "Déploiement terminé avec succès ! 🎉"

# Sauvegarder le timestamp du déploiement
echo "Dernière déploiement: ${TIMESTAMP}" > "${SCRIPT_DIR}/.last_deploy"
