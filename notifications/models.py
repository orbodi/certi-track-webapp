from django.db import models
from django.contrib.auth.models import User
from certificates.models import Certificate


class NotificationRule(models.Model):
    """
    Règles de notification pour les alertes d'expiration
    """
    
    NOTIFICATION_TYPE_CHOICES = [
        ('email', 'Email'),
        ('webhook', 'Webhook'),
        ('both', 'Email + Webhook'),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name="Nom de la règle",
        help_text="Ex: Alerte 30 jours"
    )
    
    days_before_expiration = models.IntegerField(
        verbose_name="Jours avant expiration",
        help_text="Nombre de jours avant expiration pour déclencher l'alerte"
    )
    
    notification_type = models.CharField(
        max_length=10,
        choices=NOTIFICATION_TYPE_CHOICES,
        default='email',
        verbose_name="Type de notification"
    )
    
    # Email
    email_recipients = models.TextField(
        verbose_name="Destinataires email",
        help_text="Un email par ligne",
        blank=True
    )
    
    email_subject = models.CharField(
        max_length=200,
        default="⚠️ Certificat SSL/TLS expire bientôt",
        verbose_name="Sujet de l'email"
    )
    
    # Webhook (futur)
    webhook_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL du Webhook"
    )
    
    # Filtres
    filter_by_environment = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=Certificate.ENVIRONMENT_CHOICES,
        verbose_name="Filtrer par environnement"
    )
    
    filter_by_issuer = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Filtrer par émetteur"
    )
    
    # Activation
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    # Planification
    SCHEDULE_TYPE_CHOICES = [
        ('manual', 'Manuel (via interface)'),
        ('automatic', 'Automatique (Celery Beat)'),
    ]
    
    schedule_type = models.CharField(
        max_length=10,
        choices=SCHEDULE_TYPE_CHOICES,
        default='manual',
        verbose_name="Type de planification"
    )
    
    # Pour planification automatique
    celery_task_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nom de la tâche Celery",
        help_text="Ex: notifications.tasks.send_rule_alert"
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_rules'
    )
    
    class Meta:
        ordering = ['days_before_expiration']
        verbose_name = "Règle de notification"
        verbose_name_plural = "Règles de notification"
    
    def __str__(self):
        return f"{self.name} ({self.days_before_expiration} jours)"
    
    def get_recipients_list(self):
        """Retourne la liste des emails"""
        if not self.email_recipients:
            return []
        return [email.strip() for email in self.email_recipients.split('\n') if email.strip()]
    
    def send_notification(self):
        """Envoie la notification selon la règle"""
        from .tasks import send_rule_alert
        return send_rule_alert.delay(self.id)
    
    def create_celery_task(self):
        """Crée une tâche Celery pour cette règle"""
        if self.schedule_type == 'automatic' and self.celery_task_name:
            from django_celery_beat.models import PeriodicTask, CrontabSchedule
            from django.utils import timezone
            
            # Créer ou récupérer le schedule crontab
            schedule, created = CrontabSchedule.objects.get_or_create(
                minute='0',
                hour='9',
                day_of_month='1',  # Par défaut 1er du mois
                month_of_year='*',
                day_of_week='*'
            )
            
            # Créer la tâche périodique
            task, created = PeriodicTask.objects.get_or_create(
                name=f"Règle: {self.name}",
                defaults={
                    'task': self.celery_task_name,
                    'crontab': schedule,
                    'enabled': self.is_active,
                    'args': f'[{self.id}]'  # Passer l'ID de la règle
                }
            )
            
            if not created:
                task.enabled = self.is_active
                task.save()
            
            return task
        return None


class NotificationLog(models.Model):
    """
    Historique des notifications envoyées
    """
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('sent', 'Envoyée'),
        ('failed', 'Échec'),
    ]
    
    certificate = models.ForeignKey(
        Certificate,
        on_delete=models.CASCADE,
        related_name='notification_logs',
        verbose_name="Certificat"
    )
    
    rule = models.ForeignKey(
        NotificationRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_logs',
        verbose_name="Règle appliquée"
    )
    
    notification_type = models.CharField(
        max_length=10,
        verbose_name="Type"
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
    )
    
    recipients = models.TextField(
        verbose_name="Destinataires"
    )
    
    subject = models.CharField(
        max_length=200,
        verbose_name="Sujet"
    )
    
    message = models.TextField(
        blank=True,
        verbose_name="Message"
    )
    
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="Message d'erreur"
    )
    
    sent_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Envoyé le"
    )
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Journal de notification"
        verbose_name_plural = "Journal des notifications"
    
    def __str__(self):
        return f"{self.certificate.common_name} - {self.get_status_display()} ({self.sent_at.strftime('%d/%m/%Y %H:%M')})"


class EmailSettings(models.Model):
    """
    Configuration globale des emails (singleton)
    """
    
    from_email = models.EmailField(
        default='noreply@certitrack.local',
        verbose_name="Email expéditeur"
    )
    
    from_name = models.CharField(
        max_length=100,
        default='CertiTrack',
        verbose_name="Nom expéditeur"
    )
    
    default_recipients = models.TextField(
        verbose_name="Destinataires par défaut",
        help_text="Un email par ligne (utilisé si aucune règle ne correspond)",
        blank=True
    )
    
    enable_notifications = models.BooleanField(
        default=True,
        verbose_name="Activer les notifications"
    )
    
    daily_summary_enabled = models.BooleanField(
        default=True,
        verbose_name="Résumé quotidien activé"
    )
    
    daily_summary_time = models.TimeField(
        default='08:00',
        verbose_name="Heure du résumé quotidien"
    )
    
    # Configuration SMTP
    smtp_host = models.CharField(
        max_length=255,
        default='smtp.gmail.com',
        verbose_name="Serveur SMTP",
        help_text="Ex: smtp.gmail.com, smtp.office365.com"
    )
    
    smtp_port = models.IntegerField(
        default=587,
        verbose_name="Port SMTP",
        help_text="587 (TLS) ou 465 (SSL) ou 25 (non sécurisé)"
    )
    
    smtp_use_tls = models.BooleanField(
        default=True,
        verbose_name="Utiliser TLS"
    )
    
    smtp_use_ssl = models.BooleanField(
        default=False,
        verbose_name="Utiliser SSL"
    )
    
    smtp_username = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nom d'utilisateur SMTP",
        help_text="Adresse email complète"
    )
    
    smtp_password = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Mot de passe SMTP",
        help_text="Mot de passe ou mot de passe d'application (Gmail)"
    )
    
    smtp_timeout = models.IntegerField(
        default=10,
        verbose_name="Timeout (secondes)"
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuration Email"
        verbose_name_plural = "Configuration Email"
    
    def __str__(self):
        return "Configuration des emails"
    
    def save(self, *args, **kwargs):
        # Singleton pattern
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Récupère ou crée les paramètres (singleton)"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
