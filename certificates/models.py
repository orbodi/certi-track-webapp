from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Certificate(models.Model):
    """
    Modèle pour gérer les certificats SSL/TLS
    Supporte 3 méthodes d'import: formulaire manuel, CSV, scan domaine
    """
    
    IMPORT_METHOD_CHOICES = [
        ('manual', 'Saisie Manuelle'),
        ('csv', 'Import CSV'),
        ('scan', 'Scan Domaine'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('expiring_soon', 'Expire Bientôt'),
        ('expired', 'Expiré'),
        ('revoked', 'Révoqué'),
        ('unknown', 'Inconnu'),
    ]
    
    ENVIRONMENT_CHOICES = [
        ('prod', 'Production'),
        ('uat', 'UAT'),
        ('test', 'Test'),
        ('dev', 'Développement'),
    ]
    
    # === Informations de Base (du CSV) ===
    common_name = models.CharField(
        max_length=255,
        verbose_name="Délivré à",
        help_text="Nom du serveur (ex: jenkins.eid.local)"
    )
    
    issuer = models.CharField(
        max_length=255,
        verbose_name="Délivré par",
        help_text="Autorité de certification (ex: eid-CA-01-CA)"
    )
    
    valid_until = models.DateTimeField(
        verbose_name="Date d'expiration",
        help_text="Date d'expiration du certificat"
    )
    
    key_usage = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Rôles prévus",
        help_text="Ex: Authentification du serveur"
    )
    
    friendly_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nom convivial"
    )
    
    template_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Modèle de certificat",
        help_text="Ex: CertSSLIdemia, ADFS_IDEMIA"
    )
    
    # === Informations Enrichies (scan domaine) ===
    valid_from = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Valide depuis"
    )
    
    san_list = models.JSONField(
        default=list,
        blank=True,
        verbose_name="SAN (domaines alternatifs)",
        help_text="Liste des Subject Alternative Names"
    )
    
    serial_number = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        verbose_name="Numéro de série"
    )
    
    fingerprint_sha256 = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Empreinte SHA256"
    )
    
    signature_algorithm = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Algorithme de signature"
    )
    
    public_key_size = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Taille clé publique (bits)"
    )
    
    # === Stockage Optionnel ===
    pem_data = models.TextField(
        blank=True,
        null=True,
        verbose_name="Certificat PEM",
        help_text="Contenu complet du certificat au format PEM"
    )
    
    # === Statut et Validation ===
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unknown',
        verbose_name="Statut"
    )
    
    is_self_signed = models.BooleanField(
        default=False,
        verbose_name="Auto-signé"
    )
    
    is_ca_certificate = models.BooleanField(
        default=False,
        verbose_name="Certificat CA"
    )
    
    # === Métadonnées d'Import ===
    import_method = models.CharField(
        max_length=10,
        choices=IMPORT_METHOD_CHOICES,
        verbose_name="Méthode d'import"
    )
    
    needs_enrichment = models.BooleanField(
        default=False,
        verbose_name="Nécessite enrichissement",
        help_text="Coché si le certificat doit être scanné pour enrichissement"
    )
    
    last_scanned = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Dernier scan"
    )
    
    scan_error = models.TextField(
        blank=True,
        null=True,
        verbose_name="Erreur de scan"
    )
    
    scan_port = models.IntegerField(
        default=443,
        verbose_name="Port de scan",
        help_text="Port utilisé pour le scan SSL/TLS"
    )
    
    # === Organisation ===
    environment = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=ENVIRONMENT_CHOICES,
        verbose_name="Environnement"
    )
    
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Tags",
        help_text="Tags personnalisés pour catégorisation"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    
    # === Calculs et Cache ===
    days_remaining = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Jours restants",
        help_text="Nombre de jours avant expiration (calculé automatiquement)"
    )
    
    # === Audit ===
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificates_created',
        verbose_name="Créé par"
    )
    
    class Meta:
        ordering = ['valid_until', 'common_name']
        verbose_name = "Certificat"
        verbose_name_plural = "Certificats"
        indexes = [
            models.Index(fields=['valid_until']),
            models.Index(fields=['common_name']),
            models.Index(fields=['issuer']),
            models.Index(fields=['status']),
            models.Index(fields=['environment']),
        ]
    
    def __str__(self):
        return f"{self.common_name} (expire le {self.valid_until.strftime('%d/%m/%Y')})"
    
    @property
    def days_until_expiration(self):
        """Nombre de jours avant expiration"""
        if not self.valid_until:
            return None
        delta = self.valid_until - timezone.now()
        return delta.days
    
    @property
    def is_expired(self):
        """Le certificat est-il expiré?"""
        if not self.valid_until:
            return None
        return timezone.now() > self.valid_until
    
    @property
    def is_expiring_soon(self):
        """Le certificat expire-t-il dans les 30 jours?"""
        days = self.days_until_expiration
        return days is not None and 0 < days <= 30
    
    @property
    def expiration_color(self):
        """Couleur selon l'état d'expiration (pour UI)"""
        if self.is_expired:
            return 'danger'
        elif self.is_expiring_soon:
            return 'warning'
        else:
            return 'success'
    
    def update_status(self):
        """Met à jour le statut basé sur la date d'expiration"""
        if not self.valid_until:
            self.status = 'unknown'
        elif self.is_expired:
            self.status = 'expired'
        elif self.is_expiring_soon:
            self.status = 'expiring_soon'
        else:
            self.status = 'active'
        self.save()
    
    def save(self, *args, **kwargs):
        """Override save pour mettre à jour automatiquement le statut et les jours restants"""
        if self.valid_until:
            # Calculer et stocker les jours restants
            delta = self.valid_until - timezone.now()
            self.days_remaining = delta.days
            
            # Auto-update status
            if self.is_expired:
                self.status = 'expired'
            elif self.is_expiring_soon:
                self.status = 'expiring_soon'
            elif self.status not in ['revoked']:
                self.status = 'active'
        else:
            self.days_remaining = None
        
        super().save(*args, **kwargs)
