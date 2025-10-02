#!/bin/bash

################################################################################
# Script d'installation de Bootstrap et Bootstrap Icons en local
# Pour utilisation offline de CertiTrack
################################################################################

set -e

echo "🎨 Installation de Bootstrap et Bootstrap Icons en local..."

# Créer les dossiers nécessaires
echo "📁 Création des dossiers..."
mkdir -p static/vendor/bootstrap
mkdir -p static/vendor/bootstrap-icons/fonts

# Télécharger Bootstrap CSS
echo "⬇️  Téléchargement de Bootstrap CSS..."
curl -L -o static/vendor/bootstrap/bootstrap.min.css \
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"

curl -L -o static/vendor/bootstrap/bootstrap.min.css.map \
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css.map"

# Télécharger Bootstrap JS
echo "⬇️  Téléchargement de Bootstrap JS..."
curl -L -o static/vendor/bootstrap/bootstrap.bundle.min.js \
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"

curl -L -o static/vendor/bootstrap/bootstrap.bundle.min.js.map \
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js.map"

# Télécharger Bootstrap Icons CSS
echo "⬇️  Téléchargement de Bootstrap Icons CSS..."
curl -L -o static/vendor/bootstrap-icons/bootstrap-icons.css \
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css"

# Télécharger Bootstrap Icons Fonts
echo "⬇️  Téléchargement de Bootstrap Icons Fonts..."
curl -L -o static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff \
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/fonts/bootstrap-icons.woff"

curl -L -o static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff2 \
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/fonts/bootstrap-icons.woff2"

echo ""
echo "✅ Installation terminée!"
echo ""
echo "📦 Fichiers installés:"
echo "   - static/vendor/bootstrap/bootstrap.min.css"
echo "   - static/vendor/bootstrap/bootstrap.min.css.map"
echo "   - static/vendor/bootstrap/bootstrap.bundle.min.js"
echo "   - static/vendor/bootstrap/bootstrap.bundle.min.js.map"
echo "   - static/vendor/bootstrap-icons/bootstrap-icons.css"
echo "   - static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff"
echo "   - static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff2"
echo ""
echo "🚀 Prochaine étape:"
echo "   docker-compose exec web python manage.py collectstatic --noinput"
echo ""

