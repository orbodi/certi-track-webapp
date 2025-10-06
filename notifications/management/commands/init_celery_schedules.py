"""
Commande pour initialiser les tâches planifiées Celery dans la base de données
Usage: python manage.py init_celery_schedules
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json


class Command(BaseCommand):
    help = 'Initialise les tâches planifiées Celery Beat dans la base de données'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Initialisation des tâches planifiées Celery...'))
        
        # Créer les planifications crontab
        schedules = {
            'monthly_alert_30d': self._get_or_create_schedule(hour=9, minute=0, day_of_month='1'),  # 1er du mois
            'monthly_alert_7d': self._get_or_create_schedule(hour=9, minute=0, day_of_month='24'),  # 7 jours avant fin de mois
            'daily_summary': self._get_or_create_schedule(hour=9, minute=0),
            'auto_scan': self._get_or_create_schedule(hour=2, minute=0, day_of_week='0'),  # Dimanche
            'update_days': self._get_or_create_schedule(hour=0, minute=30),  # Tous les jours à 00:30 UTC
        }
        
        # Créer ou mettre à jour les tâches périodiques
        tasks = [
            {
                'name': 'Alerte mensuelle - Certificats 30 jours',
                'task': 'notifications.tasks.monthly_alert_30_days',
                'schedule': schedules['monthly_alert_30d'],
                'enabled': True,
                'description': 'Alerte mensuelle pour les certificats expirant dans 30 jours ou moins (1er du mois)'
            },
            {
                'name': 'Alerte mensuelle - Certificats 7 jours',
                'task': 'notifications.tasks.monthly_alert_7_days',
                'schedule': schedules['monthly_alert_7d'],
                'enabled': True,
                'description': 'Alerte mensuelle pour les certificats expirant dans 7 jours ou moins (7 jours avant fin de mois)'
            },
            {
                'name': 'Résumé quotidien',
                'task': 'notifications.tasks.send_daily_summary_task',
                'schedule': schedules['daily_summary'],
                'enabled': True,
                'description': 'Envoie un résumé quotidien des certificats'
            },
            {
                'name': 'Scan automatique des certificats',
                'task': 'certificates.tasks.auto_scan_certificates',
                'schedule': schedules['auto_scan'],
                'enabled': True,
                'description': 'Scan automatique hebdomadaire des certificats (dimanche)'
            },
            {
                'name': 'Mise à jour des jours restants',
                'task': 'certificates.tasks.update_days_remaining',
                'schedule': schedules['update_days'],
                'enabled': True,
                'description': 'Met à jour quotidiennement le champ days_remaining de tous les certificats'
            },
        ]
        
        for task_data in tasks:
            task, created = PeriodicTask.objects.get_or_create(
                name=task_data['name'],
                defaults={
                    'task': task_data['task'],
                    'crontab': task_data['schedule'],
                    'enabled': task_data['enabled'],
                    'description': task_data.get('description', ''),
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Tâche créée: {task_data["name"]}'))
            else:
                # Mettre à jour si existe déjà
                task.task = task_data['task']
                task.crontab = task_data['schedule']
                task.enabled = task_data['enabled']
                task.description = task_data.get('description', '')
                task.save()
                self.stdout.write(self.style.WARNING(f'  ⟳ Tâche mise à jour: {task_data["name"]}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Initialisation terminée!'))
        self.stdout.write(self.style.SUCCESS('💡 Vous pouvez maintenant modifier les horaires via l\'interface web'))
        self.stdout.write(self.style.SUCCESS('   ou via Django Admin: /admin/django_celery_beat/periodictask/'))
    
    def _get_or_create_schedule(self, minute=0, hour=0, day_of_week='*', day_of_month='*', month_of_year='*'):
        """Crée ou récupère une planification crontab"""
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute=str(minute),
            hour=str(hour),
            day_of_week=str(day_of_week),
            day_of_month=str(day_of_month),
            month_of_year=str(month_of_year),
            timezone='UTC'
        )
        return schedule

