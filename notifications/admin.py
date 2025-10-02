from django.contrib import admin
from django import forms
from .models import NotificationRule, NotificationLog, EmailSettings


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'days_before_expiration',
        'notification_type',
        'is_active',
        'filter_by_environment',
        'created_at'
    ]
    
    list_filter = [
        'is_active',
        'notification_type',
        'filter_by_environment',
        'days_before_expiration'
    ]
    
    search_fields = ['name', 'email_recipients']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'days_before_expiration', 'is_active')
        }),
        ('Type de notification', {
            'fields': ('notification_type', 'email_subject')
        }),
        ('Destinataires Email', {
            'fields': ('email_recipients',),
            'description': 'Entrez un email par ligne'
        }),
        ('Webhook (optionnel)', {
            'fields': ('webhook_url',),
            'classes': ('collapse',)
        }),
        ('Filtres', {
            'fields': ('filter_by_environment', 'filter_by_issuer'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        'certificate',
        'notification_type',
        'status',
        'sent_at',
        'recipients_short'
    ]
    
    list_filter = [
        'status',
        'notification_type',
        'sent_at'
    ]
    
    search_fields = [
        'certificate__common_name',
        'recipients',
        'subject'
    ]
    
    readonly_fields = [
        'certificate',
        'rule',
        'notification_type',
        'status',
        'recipients',
        'subject',
        'message',
        'error_message',
        'sent_at'
    ]
    
    def recipients_short(self, obj):
        recipients = obj.recipients.split('\n')
        if len(recipients) > 1:
            return f"{recipients[0]} (+{len(recipients)-1})"
        return recipients[0] if recipients else ''
    recipients_short.short_description = 'Destinataires'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(EmailSettings)
class EmailSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Configuration Expéditeur', {
            'fields': ('from_email', 'from_name')
        }),
        ('Configuration SMTP', {
            'fields': (
                'smtp_host',
                'smtp_port',
                'smtp_username',
                'smtp_password',
                'smtp_use_tls',
                'smtp_use_ssl',
                'smtp_timeout'
            ),
            'description': 'Paramètres de connexion au serveur SMTP'
        }),
        ('Destinataires par défaut', {
            'fields': ('default_recipients',),
            'description': 'Un email par ligne'
        }),
        ('Activation', {
            'fields': ('enable_notifications',)
        }),
        ('Résumé Quotidien', {
            'fields': ('daily_summary_enabled', 'daily_summary_time')
        }),
    )
    
    def has_add_permission(self, request):
        # Singleton: ne peut créer qu'une seule instance
        return not EmailSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Masquer le mot de passe dans l'admin
        if 'smtp_password' in form.base_fields:
            form.base_fields['smtp_password'].widget = forms.PasswordInput(render_value=True)
        return form
