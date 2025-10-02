"""
Backend email dynamique utilisant les paramètres de EmailSettings
"""
from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend
from django.conf import settings


class DynamicEmailBackend(DjangoEmailBackend):
    """
    Backend email qui utilise les paramètres de EmailSettings
    au lieu des settings Django statiques
    """
    
    def __init__(self, *args, **kwargs):
        # Import ici pour éviter les imports circulaires
        from .models import EmailSettings
        
        # Récupérer les paramètres de la base de données
        email_settings = EmailSettings.get_settings()
        
        # Surcharger les paramètres avec ceux de la base
        kwargs['host'] = email_settings.smtp_host or settings.EMAIL_HOST
        kwargs['port'] = email_settings.smtp_port or settings.EMAIL_PORT
        kwargs['username'] = email_settings.smtp_username or settings.EMAIL_HOST_USER
        kwargs['password'] = email_settings.smtp_password or settings.EMAIL_HOST_PASSWORD
        kwargs['use_tls'] = email_settings.smtp_use_tls
        kwargs['use_ssl'] = email_settings.smtp_use_ssl
        kwargs['timeout'] = email_settings.smtp_timeout
        
        super().__init__(*args, **kwargs)


def get_connection():
    """
    Retourne une connexion email configurée avec les paramètres de la base
    """
    from .models import EmailSettings
    from django.core.mail import get_connection as django_get_connection
    
    email_settings = EmailSettings.get_settings()
    
    connection = django_get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host=email_settings.smtp_host,
        port=email_settings.smtp_port,
        username=email_settings.smtp_username,
        password=email_settings.smtp_password,
        use_tls=email_settings.smtp_use_tls,
        use_ssl=email_settings.smtp_use_ssl,
        timeout=email_settings.smtp_timeout,
    )
    
    return connection

