from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import NotificationRule, EmailSettings


class NotificationRuleForm(forms.ModelForm):
    """Formulaire pour créer/modifier une règle de notification"""
    
    class Meta:
        model = NotificationRule
        fields = [
            'name',
            'days_before_expiration',
            'notification_type',
            'email_recipients',
            'email_subject',
            'webhook_url',
            'filter_by_environment',
            'filter_by_issuer',
            'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'days_before_expiration': forms.NumberInput(attrs={'class': 'form-control'}),
            'notification_type': forms.Select(attrs={'class': 'form-select'}),
            'email_recipients': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'email_subject': forms.TextInput(attrs={'class': 'form-control'}),
            'webhook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'filter_by_environment': forms.Select(attrs={'class': 'form-select'}),
            'filter_by_issuer': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EmailSettingsForm(forms.ModelForm):
    """Formulaire pour configurer les paramètres email"""
    
    class Meta:
        model = EmailSettings
        fields = [
            'from_email',
            'from_name',
            'default_recipients',
            'enable_notifications',
            'daily_summary_enabled',
            'smtp_host',
            'smtp_port',
            'smtp_use_tls',
            'smtp_use_ssl',
            'smtp_username',
            'smtp_password',
            'smtp_timeout'
        ]
        widgets = {
            'from_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'from_name': forms.TextInput(attrs={'class': 'form-control'}),
            'default_recipients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'enable_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'daily_summary_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'smtp_host': forms.TextInput(attrs={'class': 'form-control'}),
            'smtp_port': forms.NumberInput(attrs={'class': 'form-control'}),
            'smtp_use_tls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'smtp_use_ssl': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'smtp_username': forms.TextInput(attrs={'class': 'form-control'}),
            'smtp_password': forms.PasswordInput(attrs={'class': 'form-control', 'render_value': True}),
            'smtp_timeout': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class CeleryTaskForm(forms.Form):
    """Formulaire pour créer/modifier une tâche Celery planifiée"""
    
    name = forms.CharField(
        label="Nom de la tâche",
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Vérification quotidienne'
        })
    )
    
    task = forms.CharField(
        label="Nom de la tâche Python",
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: notifications.tasks.check_certificate_expirations'
        }),
        help_text="Format: app.module.fonction"
    )
    
    description = forms.CharField(
        label="Description",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Description de la tâche'
        })
    )
    
    schedule_type = forms.ChoiceField(
        label="Type de planification",
        choices=[
            ('crontab', 'Crontab (horaire fixe)'),
            ('interval', 'Intervalle (répétitif)')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='crontab'
    )
    
    # Champs Crontab
    crontab_minute = forms.CharField(
        label="Minutes",
        initial='0',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0-59 ou *'
        }),
        help_text="0-59 ou * pour toutes les minutes"
    )
    
    crontab_hour = forms.CharField(
        label="Heures",
        initial='8',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0-23 ou *'
        }),
        help_text="0-23 ou * pour toutes les heures"
    )
    
    crontab_day_of_week = forms.CharField(
        label="Jour de la semaine",
        initial='*',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0-6 ou *'
        }),
        help_text="0 (dimanche) à 6 (samedi) ou * pour tous les jours"
    )
    
    crontab_day_of_month = forms.CharField(
        label="Jour du mois",
        initial='*',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1-31 ou *'
        }),
        help_text="1-31 ou * pour tous les jours"
    )
    
    crontab_month_of_year = forms.CharField(
        label="Mois de l'année",
        initial='*',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1-12 ou *'
        }),
        help_text="1-12 ou * pour tous les mois"
    )
    
    # Champs Intervalle
    interval_every = forms.IntegerField(
        label="Chaque",
        initial=1,
        required=False,
        validators=[MinValueValidator(1)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1'
        })
    )
    
    interval_period = forms.ChoiceField(
        label="Période",
        required=False,
        choices=[
            ('seconds', 'Secondes'),
            ('minutes', 'Minutes'),
            ('hours', 'Heures'),
            ('days', 'Jours'),
            ('weeks', 'Semaines'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='hours'
    )
    
    enabled = forms.BooleanField(
        label="Tâche activée",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    one_off = forms.BooleanField(
        label="Exécution unique (one-off)",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="La tâche sera exécutée une seule fois puis désactivée"
    )
    
    args = forms.CharField(
        label="Arguments (JSON)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': '[]'
        }),
        help_text='Format JSON, ex: [1, "text"]',
        initial='[]'
    )
    
    kwargs = forms.CharField(
        label="Arguments nommés (JSON)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': '{}'
        }),
        help_text='Format JSON, ex: {"key": "value"}',
        initial='{}'
    )
    
    def clean_args(self):
        """Valider que args est du JSON valide"""
        import json
        args = self.cleaned_data.get('args', '[]')
        if not args:
            return '[]'
        try:
            json.loads(args)
            return args
        except json.JSONDecodeError:
            raise forms.ValidationError("Format JSON invalide")
    
    def clean_kwargs(self):
        """Valider que kwargs est du JSON valide"""
        import json
        kwargs = self.cleaned_data.get('kwargs', '{}')
        if not kwargs:
            return '{}'
        try:
            json.loads(kwargs)
            return kwargs
        except json.JSONDecodeError:
            raise forms.ValidationError("Format JSON invalide")
