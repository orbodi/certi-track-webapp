#!/bin/bash

################################################################################
# Script d'installation des prérequis pour CertiTrack
# Description : Installe Docker et Docker Compose sur Ubuntu/Debian
# Usage : sudo ./install-prereqs.sh
################################################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifier que le script est exécuté en tant que root
if [ "$EUID" -ne 0 ]; then 
    error "Ce script doit être exécuté avec sudo"
    exit 1
fi

info "Installation des prérequis pour CertiTrack sur Ubuntu/Debian..."
echo ""

# Mise à jour du système
info "Mise à jour du système..."
apt-get update -qq
apt-get upgrade -y -qq
success "Système mis à jour"
echo ""

# Installation de Docker
if command -v docker &> /dev/null; then
    success "Docker est déjà installé ($(docker --version))"
else
    info "Installation de Docker..."
    
    # Installer les dépendances
    apt-get install -y -qq \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Ajouter la clé GPG officielle de Docker
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Configurer le dépôt
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Installer Docker Engine
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Démarrer et activer Docker
    systemctl start docker
    systemctl enable docker
    
    success "Docker installé avec succès"
fi
echo ""

# Installation de Docker Compose
if command -v docker-compose &> /dev/null; then
    success "Docker Compose est déjà installé ($(docker-compose --version))"
else
    info "Installation de Docker Compose..."
    
    # Installer Docker Compose v2
    apt-get install -y -qq docker-compose-plugin
    
    # Créer un alias pour la compatibilité
    if ! grep -q "alias docker-compose" /etc/bash.bashrc; then
        echo "alias docker-compose='docker compose'" >> /etc/bash.bashrc
    fi
    
    success "Docker Compose installé avec succès"
fi
echo ""

# Ajouter l'utilisateur actuel au groupe docker
REAL_USER=${SUDO_USER:-$USER}
if groups $REAL_USER | grep &>/dev/null '\bdocker\b'; then
    success "L'utilisateur $REAL_USER est déjà dans le groupe docker"
else
    info "Ajout de l'utilisateur $REAL_USER au groupe docker..."
    usermod -aG docker $REAL_USER
    success "Utilisateur ajouté au groupe docker"
    warning "Déconnectez-vous et reconnectez-vous pour que les changements prennent effet"
fi
echo ""

# Installation de Git (si nécessaire)
if command -v git &> /dev/null; then
    success "Git est déjà installé ($(git --version))"
else
    info "Installation de Git..."
    apt-get install -y -qq git
    success "Git installé avec succès"
fi
echo ""

# Installation d'outils utiles
info "Installation d'outils utiles..."
apt-get install -y -qq curl wget nano vim htop
success "Outils installés"
echo ""

# Vérification finale
echo ""
info "Vérification de l'installation..."
echo ""
echo "Docker version:"
docker --version
echo ""
echo "Docker Compose version:"
docker compose version || docker-compose --version
echo ""

success "✅ Installation terminée avec succès !"
echo ""
warning "⚠️  IMPORTANT : Déconnectez-vous et reconnectez-vous pour que les modifications du groupe docker prennent effet"
echo ""
info "Vous pouvez maintenant déployer CertiTrack avec : ./deploy.sh"

