"""
Configuration Celery pour CertiTrack
"""
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('certitrack')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Utiliser django-celery-beat pour la planification dynamique
# Les tâches planifiées sont maintenant gérées dans la base de données
# et configurables via l'interface web
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'

# Timezone
app.conf.timezone = 'UTC'

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


