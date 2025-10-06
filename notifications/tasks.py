"""
Tâches Celery pour les notifications
"""
from celery import shared_task
from django.core.management import call_command
from django.core.mail import EmailMessage
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


@shared_task(name='notifications.tasks.monthly_alert_30_days')
def monthly_alert_30_days():
    """
    Tâche Celery pour l'alerte mensuelle des certificats expirant dans 30 jours ou moins
    Exécutée le 1er de chaque mois
    """
    from django.core.mail import EmailMessage
    from .email_backend import get_connection
    from certificates.models import Certificate
    from .models import EmailSettings
    from django.utils import timezone
    
    try:
        email_settings = EmailSettings.get_settings()
        
        # Récupérer tous les certificats expirant dans 30 jours ou moins
        certificates = Certificate.objects.filter(
            status__in=['active', 'expiring_soon'],
            days_remaining__lte=30,
            days_remaining__gte=0
        ).order_by('days_remaining')
        
        if not certificates.exists():
            return 'Aucun certificat à notifier pour l\'alerte 30 jours'
        
        # Préparer les destinataires
        recipients = email_settings.default_recipients.split('\n')
        recipients = [email.strip() for email in recipients if email.strip()]
        
        if not recipients:
            return 'Aucun destinataire configuré'
        
        # Créer le contenu email
        cert_list = ""
        for cert in certificates:
            cert_list += f"- {cert.common_name} (Expire le {cert.valid_until.strftime('%d/%m/%Y')})\n"
        
        body_content = f"""Bonjour,

Voici la liste des certificats arrivant à échéance dans les 30 prochains jours :

{cert_list}
Action requise : renouveler ces certificats afin d'éviter toute interruption de service.

Message automatique – merci de ne pas répondre.

Cordialement,
CertiTrack"""
        
        # Envoyer l'email
        connection = get_connection()
        email = EmailMessage(
            subject='Alerte Mensuelle - Certificats expirant dans 30 jours',
            body=body_content,
            from_email=f'{email_settings.from_name} <{email_settings.from_email}>',
            to=recipients,
            connection=connection
        )
        email.encoding = 'utf-8'
        email.content_subtype = 'plain'
        email.send(fail_silently=False)
        
        return f'Alerte mensuelle 30 jours envoyée pour {certificates.count()} certificat(s)'
        
    except Exception as e:
        return f'Erreur lors de l\'envoi de l\'alerte mensuelle 30 jours: {str(e)}'


@shared_task(name='notifications.tasks.monthly_alert_7_days')
def monthly_alert_7_days():
    """
    Tâche Celery pour l'alerte mensuelle des certificats expirant dans 7 jours ou moins
    Exécutée 7 jours avant la fin du mois
    """
    from django.core.mail import EmailMessage
    from .email_backend import get_connection
    from certificates.models import Certificate
    from .models import EmailSettings
    from django.utils import timezone
    
    try:
        email_settings = EmailSettings.get_settings()
        
        # Récupérer tous les certificats expirant dans 7 jours ou moins
        certificates = Certificate.objects.filter(
            status__in=['active', 'expiring_soon'],
            days_remaining__lte=7,
            days_remaining__gte=0
        ).order_by('days_remaining')
        
        if not certificates.exists():
            return 'Aucun certificat à notifier pour l\'alerte 7 jours'
        
        # Préparer les destinataires
        recipients = email_settings.default_recipients.split('\n')
        recipients = [email.strip() for email in recipients if email.strip()]
        
        if not recipients:
            return 'Aucun destinataire configuré'
        
        # Créer le contenu email
        cert_list = ""
        for cert in certificates:
            cert_list += f"- {cert.common_name} (Expire le {cert.valid_until.strftime('%d/%m/%Y')})\n"
        
        body_content = f"""Bonjour,

Voici la liste des certificats arrivant à échéance dans les 7 prochains jours :

{cert_list}
Action requise : renouveler ces certificats afin d'éviter toute interruption de service.

Message automatique – merci de ne pas répondre.

Cordialement,
CertiTrack"""
        
        # Envoyer l'email
        connection = get_connection()
        email = EmailMessage(
            subject='Alerte Mensuelle - Certificats expirant dans 7 jours',
            body=body_content,
            from_email=f'{email_settings.from_name} <{email_settings.from_email}>',
            to=recipients,
            connection=connection
        )
        email.encoding = 'utf-8'
        email.content_subtype = 'plain'
        email.send(fail_silently=False)
        
        return f'Alerte mensuelle 7 jours envoyée pour {certificates.count()} certificat(s)'
        
    except Exception as e:
        return f'Erreur lors de l\'envoi de l\'alerte mensuelle 7 jours: {str(e)}'


@shared_task(name='notifications.tasks.send_rule_alert')
def send_rule_alert(rule_id):
    """
    Tâche Celery pour envoyer une alerte selon une règle de notification
    """
    try:
        rule = NotificationRule.objects.get(id=rule_id)
        email_settings = EmailSettings.get_settings()
        
        # Récupérer les certificats selon la règle
        certificates = Certificate.objects.filter(
            status__in=['active', 'expiring_soon'],
            days_remaining__lte=rule.days_before_expiration,
            days_remaining__gte=0
        )
        
        # Appliquer les filtres de la règle
        if rule.filter_by_environment:
            certificates = certificates.filter(environment=rule.filter_by_environment)
        
        if rule.filter_by_issuer:
            certificates = certificates.filter(issuer__icontains=rule.filter_by_issuer)
        
        if not certificates.exists():
            return f'Aucun certificat trouvé pour la règle {rule.name}'
        
        # Préparer les destinataires
        recipients = rule.get_recipients_list()
        if not recipients:
            recipients = email_settings.default_recipients.split('\n')
            recipients = [email.strip() for email in recipients if email.strip()]
        
        if not recipients:
            return 'Aucun destinataire configuré'
        
        # Créer le contenu email
        cert_list = ""
        for cert in certificates:
            cert_list += f"- {cert.common_name} (Expire le {cert.valid_until.strftime('%d/%m/%Y')})\n"
        
        body_content = f"""Bonjour,

Voici la liste des certificats arrivant à échéance dans les {rule.days_before_expiration} prochains jours :

{cert_list}
Action requise : renouveler ces certificats afin d'éviter toute interruption de service.

Message automatique – merci de ne pas répondre.

Cordialement,
CertiTrack"""
        
        # Envoyer l'email
        connection = get_connection()
        email = EmailMessage(
            subject=rule.email_subject,
            body=body_content,
            from_email=f'{email_settings.from_name} <{email_settings.from_email}>',
            to=recipients,
            connection=connection
        )
        email.encoding = 'utf-8'
        email.content_subtype = 'plain'
        email.send(fail_silently=False)
        
        # Logger le succès pour chaque certificat
        for cert in certificates:
            NotificationLog.objects.create(
                certificate=cert,
                rule=rule,
                status='sent',
                message=f'Alerte groupée envoyée pour {certificates.count()} certificat(s)'
            )
        
        return f'Alerte de la règle {rule.name} envoyée pour {certificates.count()} certificat(s)'
        
    except Exception as e:
        # Logger l'erreur
        try:
            NotificationLog.objects.create(
                rule=rule,
                status='error',
                message=str(e)
            )
        except:
            pass
        
        return f'Erreur lors de l\'envoi de la règle {rule_id}: {str(e)}'


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
        
        # Créer le contenu email directement avec formatage forcé
        from_email = f'{email_settings.from_name} <{email_settings.from_email}>'
        
        # Contenu email avec nouveau format et dates en gras
        body_content = f"""Objet : Alerte – Certificats en expiration

Bonjour,

Voici la liste des certificats arrivant à échéance dans les prochains jours :

Certificat	Date d'expiration
{certificate.common_name}	**{certificate.valid_until.strftime('%d/%m/%Y')}**

Action requise : renouveler ces certificats afin d'éviter toute interruption de service.

Message automatique – merci de ne pas répondre.

Cordialement,
CertiTrack"""
        
        # Envoyer seulement du texte simple avec encodage UTF-8 explicite
        email = EmailMessage(
            subject=rule.email_subject,
            body=body_content,
            from_email=from_email,
            to=recipients,
            connection=connection
        )
        # Forcer l'encodage UTF-8 et le type de contenu
        email.encoding = 'utf-8'
        email.content_subtype = 'plain'
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

