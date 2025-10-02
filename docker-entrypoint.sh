#!/bin/bash
# Script de démarrage pour le conteneur Docker

set -e

echo "Waiting for PostgreSQL..."
until nc -z db 5444 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is up - continuing"

# Exécuter les commandes d'initialisation uniquement pour le service web
if [ "$SERVICE_NAME" = "web" ]; then
    echo "Applying database migrations..."
    python manage.py migrate --noinput

    echo "Collecting static files..."
    python manage.py collectstatic --noinput

    echo "Creating superuser if needed..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin');
    print('Superuser created: admin/admin');
else:
    print('Superuser already exists');
" || true

    echo "Initializing notification rules..."
    python manage.py init_notification_rules --email admin@example.com || true
else
    echo "Skipping initialization (not web service)"
    # Attendre que les migrations soient appliquées par le service web
    sleep 5
fi

echo "Starting application..."
exec "$@"

