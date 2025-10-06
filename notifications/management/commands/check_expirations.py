"""
Commande pour vérifier les certificats expirant et envoyer des alertes groupées
Usage: python manage.py check_expirations [--dry-run] [--force]
"""
from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from urllib.parse import urlencode

from certificates.models import Certificate
from notifications.models import NotificationRule, NotificationLog, EmailSettings


class Command(BaseCommand):
    help = 'Vérifie les certificats expirant et envoie des alertes groupées par règle'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les alertes sans les envoyer',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force l\'envoi même si déjà envoyé aujourd\'hui',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        # Récupérer les paramètres
        email_settings = EmailSettings.get_settings()
        
        if not email_settings.enable_notifications and not dry_run:
            self.stdout.write(self.style.WARNING(
                '⚠️  Les notifications sont désactivées dans les paramètres'
            ))
            return
        
        # Récupérer les règles actives
        rules = NotificationRule.objects.filter(is_active=True)
        
        if not rules.exists():
            self.stdout.write(self.style.WARNING(
                '⚠️  Aucune règle de notification active'
            ))
            return
        
        self.stdout.write(self.style.SUCCESS(
            f'🔍 Vérification des certificats avec {rules.count()} règle(s) active(s)...'
        ))
        
        total_sent = 0
        total_errors = 0
        
        # Pour chaque règle
        for rule in rules:
            self.stdout.write(f'\n📋 Règle: {rule.name} ({rule.days_before_expiration} jours)')
            
            # Utiliser le champ days_remaining en base de données pour des requêtes performantes
            # Inclure tous les certificats qui expirent dans X jours OU MOINS
            certificates = Certificate.objects.filter(
                status__in=['active', 'expiring_soon'],
                days_remaining__lte=rule.days_before_expiration,
                days_remaining__gte=0  # Exclure les certificats déjà expirés
            )
            
            # Appliquer les filtres de la règle
            if rule.filter_by_environment:
                certificates = certificates.filter(environment=rule.filter_by_environment)
            
            if rule.filter_by_issuer:
                certificates = certificates.filter(issuer__icontains=rule.filter_by_issuer)
            
            if not certificates.exists():
                self.stdout.write(self.style.SUCCESS(
                    f'   ✓ Aucun certificat trouvé pour cette règle'
                ))
                continue
            
            self.stdout.write(self.style.WARNING(
                f'   ⚠️  {certificates.count()} certificat(s) trouvé(s)'
            ))
            
            # Vérifier si une notification groupée n'a pas déjà été envoyée aujourd'hui pour cette règle
            if not force:
                today = timezone.now().date()
                # On vérifie si au moins un certificat de cette règle a déjà été notifié aujourd'hui
                already_sent_today = NotificationLog.objects.filter(
                    rule=rule,
                    sent_at__date=today,
                    status='sent',
                    certificate__in=certificates
                ).exists()
                
                if already_sent_today:
                    self.stdout.write(
                        f'   → Notification groupée déjà envoyée aujourd\'hui pour cette règle'
                    )
                    continue
            
            # Préparer les destinataires
            recipients = rule.get_recipients_list()
            if not recipients:
                recipients = email_settings.default_recipients.split('\n')
                recipients = [email.strip() for email in recipients if email.strip()]
            
            if not recipients:
                self.stdout.write(self.style.ERROR(
                    f'   ✗ Aucun destinataire configuré pour cette règle'
                ))
                continue
            
            # Base URL
            base_url = f'http://{settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "localhost:8000"}'
            
            # Construire l'URL filtrée pour la liste des certificats
            filter_params = {'days': rule.days_before_expiration}
            if rule.filter_by_environment:
                filter_params['environment'] = rule.filter_by_environment
            if rule.filter_by_issuer:
                filter_params['issuer'] = rule.filter_by_issuer
            
            certificates_list_url = f'{base_url}/certificates/?{urlencode(filter_params)}'
            
            # Contexte pour le template d'email groupé
            context = {
                'certificates': list(certificates),
                'days_before_expiration': rule.days_before_expiration,
                'rule': rule,
                'current_date': timezone.now(),
                'base_url': base_url,
                'certificates_list_url': certificates_list_url,
            }
            
            if dry_run:
                self.stdout.write(self.style.SUCCESS(
                    f'   [DRY-RUN] Email groupé pour {certificates.count()} certificat(s) → {", ".join(recipients)}'
                ))
                for cert in certificates:
                    self.stdout.write(f'      - {cert.common_name}')
                continue
            
            # Envoyer l'email groupé
            try:
                # Utiliser la connexion avec les paramètres de la base
                from notifications.email_backend import get_connection
                connection = get_connection()
                
                # Créer l'email
                from_email = f'{email_settings.from_name} <{email_settings.from_email}>'
                
                # Subject personnalisé avec le nombre de certificats
                if certificates.count() == 1:
                    subject = rule.email_subject
                else:
                    subject = f"{rule.email_subject} - {certificates.count()} certificats"
                
                # Créer le contenu email directement avec formatage forcé
                cert_list = ""
                for cert in certificates:
                    cert_list += f"- {cert.common_name} (Expire le {cert.valid_until.strftime('%d/%m/%Y')})\n"
                
                body_content = f"""Bonjour,

Voici la liste des certificats arrivant à échéance dans les prochains jours :

{cert_list}
Action requise : renouveler ces certificats afin d'éviter toute interruption de service.

Message automatique – merci de ne pas répondre.

Cordialement,
CertiTrack"""
                
                # Envoyer seulement du texte simple avec encodage UTF-8 explicite
                email = EmailMessage(
                    subject=subject,
                    body=body_content,
                    from_email=from_email,
                    to=recipients,
                    connection=connection
                )
                # Forcer l'encodage UTF-8 et le type de contenu
                email.encoding = 'utf-8'
                email.content_subtype = 'plain'
                
                # Envoyer
                email.send(fail_silently=False)
                
                # Logger le succès pour chaque certificat
                for cert in certificates:
                    NotificationLog.objects.create(
                        certificate=cert,
                        rule=rule,
                        notification_type='email',
                        status='sent',
                        recipients='\n'.join(recipients),
                        subject=subject,
                        message=f"Email groupé avec {certificates.count()} certificat(s)"
                    )
                
                self.stdout.write(self.style.SUCCESS(
                    f'   ✓ Email groupé envoyé pour {certificates.count()} certificat(s) à {len(recipients)} destinataire(s)'
                ))
                total_sent += 1
                
            except Exception as e:
                # Logger l'erreur pour chaque certificat
                for cert in certificates:
                    NotificationLog.objects.create(
                        certificate=cert,
                        rule=rule,
                        notification_type='email',
                        status='failed',
                        recipients='\n'.join(recipients),
                        subject=subject if 'subject' in locals() else rule.email_subject,
                        error_message=str(e)
                    )
                
                self.stdout.write(self.style.ERROR(
                    f'   ✗ Erreur lors de l\'envoi groupé - {str(e)}'
                ))
                total_errors += 1
        
        # Résumé
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'🎯 Mode DRY-RUN: {total_sent} notification(s) groupée(s) seraient envoyée(s)'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'✅ {total_sent} notification(s) groupée(s) envoyée(s)'
            ))
            if total_errors:
                self.stdout.write(self.style.ERROR(
                    f'❌ {total_errors} erreur(s)'
                ))
