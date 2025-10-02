"""
Commande pour envoyer le résumé quotidien
Usage: python manage.py send_daily_summary [--dry-run]
"""
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings

from certificates.models import Certificate
from notifications.models import EmailSettings


class Command(BaseCommand):
    help = 'Envoie le résumé quotidien des certificats'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche le résumé sans l\'envoyer',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Récupérer les paramètres
        email_settings = EmailSettings.get_settings()
        
        if not email_settings.daily_summary_enabled and not dry_run:
            self.stdout.write(self.style.WARNING(
                '⚠️  Le résumé quotidien est désactivé'
            ))
            return
        
        if not email_settings.enable_notifications and not dry_run:
            self.stdout.write(self.style.WARNING(
                '⚠️  Les notifications sont désactivées'
            ))
            return
        
        # Statistiques
        stats = {
            'total': Certificate.objects.count(),
            'active': Certificate.objects.filter(status='active').count(),
            'expiring_soon': Certificate.objects.filter(status='expiring_soon').count(),
            'expired': Certificate.objects.filter(status='expired').count(),
        }
        
        # Certificats expirant bientôt (30 jours)
        expiring_certs = Certificate.objects.filter(
            status='expiring_soon'
        ).order_by('valid_until')[:10]  # Top 10
        
        # Certificats expirés
        expired_certs = Certificate.objects.filter(
            status='expired'
        ).order_by('-valid_until')[:5]  # Top 5
        
        # Destinataires
        recipients = email_settings.default_recipients.split('\n')
        recipients = [email.strip() for email in recipients if email.strip()]
        
        if not recipients:
            self.stdout.write(self.style.ERROR(
                '❌ Aucun destinataire configuré pour le résumé quotidien'
            ))
            return
        
        # Contexte
        context = {
            'stats': stats,
            'expiring_certs': expiring_certs,
            'expired_certs': expired_certs,
            'current_date': timezone.now(),
            'dashboard_url': f'http://{settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "localhost:8000"}/certificates/'
        }
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('='*60))
            self.stdout.write(self.style.SUCCESS('📊 RÉSUMÉ QUOTIDIEN (DRY-RUN)'))
            self.stdout.write(self.style.SUCCESS('='*60))
            self.stdout.write(f'\nStatistiques:')
            self.stdout.write(f'  • Total: {stats["total"]}')
            self.stdout.write(f'  • Actifs: {stats["active"]}')
            self.stdout.write(f'  • Expire Bientôt: {stats["expiring_soon"]}')
            self.stdout.write(f'  • Expirés: {stats["expired"]}')
            
            if expiring_certs:
                self.stdout.write(f'\n⚠️  Certificats expirant bientôt: {expiring_certs.count()}')
                for cert in expiring_certs:
                    self.stdout.write(f'   • {cert.common_name} ({cert.days_until_expiration} jours)')
            
            if expired_certs:
                self.stdout.write(f'\n❌ Certificats expirés: {expired_certs.count()}')
                for cert in expired_certs:
                    self.stdout.write(f'   • {cert.common_name}')
            
            self.stdout.write(f'\n📧 Destinataires: {", ".join(recipients)}')
            self.stdout.write(self.style.SUCCESS('\n✓ Mode DRY-RUN: Aucun email envoyé'))
            return
        
        try:
            # Utiliser la connexion avec les paramètres de la base
            from notifications.email_backend import get_connection
            connection = get_connection()
            
            # Rendu des templates
            html_content = render_to_string('emails/daily_summary.html', context)
            
            # Créer l'email
            from_email = f'{email_settings.from_name} <{email_settings.from_email}>'
            subject = f'📊 CertiTrack - Résumé Quotidien ({timezone.now().strftime("%d/%m/%Y")})'
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=f'Résumé quotidien des certificats SSL/TLS\n\n'
                     f'Total: {stats["total"]} | Expire Bientôt: {stats["expiring_soon"]} | Expirés: {stats["expired"]}',
                from_email=from_email,
                to=recipients,
                connection=connection
            )
            email.attach_alternative(html_content, "text/html")
            
            # Envoyer
            email.send(fail_silently=False)
            
            self.stdout.write(self.style.SUCCESS(
                f'✅ Résumé quotidien envoyé à {len(recipients)} destinataire(s)'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'❌ Erreur lors de l\'envoi: {str(e)}'
            ))

