"""
Commande pour initialiser les règles de notification par défaut
Usage: python manage.py init_notification_rules
"""
from django.core.management.base import BaseCommand
from notifications.models import NotificationRule, EmailSettings


class Command(BaseCommand):
    help = 'Initialise les règles de notification par défaut (30j et 7j)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email destinataire par défaut',
        )
    
    def handle(self, *args, **options):
        email = options.get('email')
        
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('Initialisation des Regles de Notification'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # Créer ou mettre à jour la configuration email
        email_settings = EmailSettings.get_settings()
        
        if email:
            email_settings.default_recipients = email
            email_settings.save()
            self.stdout.write(self.style.SUCCESS(f'\n[OK] Email par defaut configure: {email}'))
        
        # Règle 1: Alerte 30 jours avant expiration
        rule1, created1 = NotificationRule.objects.get_or_create(
            name='Alerte 30 jours',
            days_before_expiration=30,
            defaults={
                'notification_type': 'email',
                'email_subject': '⚠️ Certificat expire dans 30 jours',
                'email_recipients': email if email else '',
                'is_active': True,
            }
        )
        
        if created1:
            self.stdout.write(self.style.SUCCESS('[OK] Regle creee: Alerte 30 jours avant expiration'))
        else:
            self.stdout.write(self.style.WARNING('Regle existante: Alerte 30 jours'))
        
        # Règle 2: Alerte 7 jours avant expiration (URGENT)
        rule2, created2 = NotificationRule.objects.get_or_create(
            name='Alerte 7 jours (URGENT)',
            days_before_expiration=7,
            defaults={
                'notification_type': 'email',
                'email_subject': '🚨 URGENT - Certificat expire dans 7 jours',
                'email_recipients': email if email else '',
                'is_active': True,
            }
        )
        
        if created2:
            self.stdout.write(self.style.SUCCESS('[OK] Regle creee: Alerte 7 jours avant expiration (URGENT)'))
        else:
            self.stdout.write(self.style.WARNING('Regle existante: Alerte 7 jours'))
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Configuration terminee!'))
        self.stdout.write('='*60)
        
        self.stdout.write('\nRESUME:')
        self.stdout.write(f'   {NotificationRule.objects.filter(is_active=True).count()} regle(s) active(s)')
        self.stdout.write(f'   Notifications: {"Activees" if email_settings.enable_notifications else "Desactivees"}')
        self.stdout.write(f'   Resume quotidien: {"Active" if email_settings.daily_summary_enabled else "Desactive"}')
        
        if email_settings.default_recipients:
            self.stdout.write(f'   Destinataires: {email_settings.default_recipients}')
        else:
            self.stdout.write(self.style.WARNING('   Aucun destinataire configure!'))
        
        self.stdout.write('\nPROCHAINES ETAPES:')
        self.stdout.write('   1. Configurez vos emails SMTP dans settings.py ou .env')
        self.stdout.write('   2. Testez avec: python manage.py check_expirations --dry-run')
        self.stdout.write('   3. Ajoutez des destinataires dans l\'admin: http://localhost:8000/admin/')
        self.stdout.write('   4. Lancez le worker Celery pour automatisation (optionnel)')
        
        self.stdout.write('')

