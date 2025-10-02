"""
Tâches Celery pour les notifications
"""
from celery import shared_task
from django.core.management import call_command
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

from certificates.models import Certificate
from .models import NotificationRule, NotificationLog, EmailSettings


@shared_task(name='notifications.tasks.check_certificate_expirations')
def check_certificate_expirations():
    """
    Tâche Celery pour vérifier les certificats expirant
    Appelée quotidiennement par Celery Beat
    """
    try:
        # Appeler la commande Django
        call_command('check_expirations')
        return 'Vérification des expirations terminée avec succès'
    except Exception as e:
        return f'Erreur lors de la vérification: {str(e)}'


@shared_task(name='notifications.tasks.send_daily_summary_task')
def send_daily_summary_task():
    """
    Tâche Celery pour envoyer le résumé quotidien
    Appelée quotidiennement par Celery Beat
    """
    try:
        call_command('send_daily_summary')
        return 'Résumé quotidien envoyé avec succès'
    except Exception as e:
        return f'Erreur lors de l\'envoi du résumé: {str(e)}'


@shared_task(name='notifications.tasks.send_certificate_alert')
def send_certificate_alert(certificate_id, rule_id):
    """
    Tâche Celery pour envoyer une alerte pour un certificat spécifique
    """
    try:
        certificate = Certificate.objects.get(id=certificate_id)
        rule = NotificationRule.objects.get(id=rule_id)
        email_settings = EmailSettings.get_settings()
        
        # Préparer les destinataires
        recipients = rule.get_recipients_list()
        if not recipients:
            recipients = email_settings.default_recipients.split('\n')
            recipients = [email.strip() for email in recipients if email.strip()]
        
        if not recipients:
            return 'Aucun destinataire configuré'
        
        # Récupérer les autres certificats expirant bientôt
        from certificates.models import Certificate as Cert
        other_expiring = Cert.objects.filter(
            status='expiring_soon'
        ).exclude(pk=certificate.pk).order_by('valid_until')[:5]
        
        # Base URL
        base_url = f'http://{settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "localhost:8000"}'
        
        # Contexte pour le template
        context = {
            'certificate': certificate,
            'days_until_expiration': certificate.days_until_expiration,
            'rule': rule,
            'current_date': timezone.now(),
            'cert_url': f'{base_url}/certificates/{certificate.pk}/',
            'base_url': base_url,
            'other_expiring_certs': other_expiring,
        }
        
        # Utiliser la connexion avec les paramètres de la base
        from .email_backend import get_connection
        connection = get_connection()
        
        # Rendu des templates
        html_content = render_to_string('emails/certificate_expiring.html', context)
        text_content = render_to_string('emails/certificate_expiring.txt', context)
        
        # Créer et envoyer l'email
        from_email = f'{email_settings.from_name} <{email_settings.from_email}>'
        
        email = EmailMultiAlternatives(
            subject=rule.email_subject,
            body=text_content,
            from_email=from_email,
            to=recipients,
            connection=connection
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        # Logger le succès
        NotificationLog.objects.create(
            certificate=certificate,
            rule=rule,
            notification_type='email',
            status='sent',
            recipients='\n'.join(recipients),
            subject=rule.email_subject,
            message=text_content
        )
        
        return f'Alerte envoyée pour {certificate.common_name}'
        
    except Certificate.DoesNotExist:
        return f'Certificat {certificate_id} introuvable'
    except NotificationRule.DoesNotExist:
        return f'Règle {rule_id} introuvable'
    except Exception as e:
        # Logger l'erreur
        if 'certificate' in locals() and 'rule' in locals():
            NotificationLog.objects.create(
                certificate=certificate,
                rule=rule,
                notification_type='email',
                status='failed',
                recipients='\n'.join(recipients) if 'recipients' in locals() else '',
                subject=rule.email_subject if 'rule' in locals() else '',
                error_message=str(e)
            )
        return f'Erreur: {str(e)}'


@shared_task(name='notifications.tasks.test_email_configuration')
def test_email_configuration(recipient_email):
    """
    Tâche pour tester la configuration email
    """
    try:
        from .email_backend import get_connection
        email_settings = EmailSettings.get_settings()
        connection = get_connection()
        from_email = f'{email_settings.from_name} <{email_settings.from_email}>'
        
        subject = '✅ Test CertiTrack - Configuration Email'
        message = f'''
Bonjour,

Ceci est un email de test pour vérifier la configuration de CertiTrack.

Si vous recevez cet email, la configuration est correcte ! ✓

Date: {timezone.now().strftime("%d/%m/%Y %H:%M")}

---
CertiTrack - Gestion des Certificats SSL/TLS
        '''
        
        from django.core.mail import EmailMessage
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=[recipient_email],
            connection=connection
        )
        email.send(fail_silently=False)
        
        return f'Email de test envoyé à {recipient_email}'
        
    except Exception as e:
        return f'Erreur lors de l\'envoi: {str(e)}'

