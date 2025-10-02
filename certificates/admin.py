from django.contrib import admin
from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = [
        'common_name',
        'issuer',
        'valid_until',
        'status',
        'environment',
        'import_method',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'environment',
        'import_method',
        'is_self_signed',
        'created_at',
    ]
    
    search_fields = [
        'common_name',
        'issuer',
        'serial_number',
        'template_name',
        'notes',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'last_scanned',
        'days_until_expiration',
        'is_expired',
    ]
    
    fieldsets = (
        ('Informations de base', {
            'fields': (
                'common_name',
                'issuer',
                'valid_from',
                'valid_until',
                'key_usage',
                'friendly_name',
                'template_name',
            )
        }),
        ('Détails techniques', {
            'fields': (
                'serial_number',
                'fingerprint_sha256',
                'signature_algorithm',
                'public_key_size',
                'san_list',
                'pem_data',
            ),
            'classes': ('collapse',)
        }),
        ('Statut et validation', {
            'fields': (
                'status',
                'is_self_signed',
                'is_ca_certificate',
                'days_until_expiration',
                'is_expired',
            )
        }),
        ('Métadonnées d\'import', {
            'fields': (
                'import_method',
                'needs_enrichment',
                'last_scanned',
                'scan_error',
                'scan_port',
            )
        }),
        ('Organisation', {
            'fields': (
                'environment',
                'tags',
                'notes',
            )
        }),
        ('Audit', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['update_status', 'mark_for_enrichment']
    
    def update_status(self, request, queryset):
        for cert in queryset:
            cert.update_status()
        self.message_user(request, f'{queryset.count()} certificats mis à jour')
    update_status.short_description = "Mettre à jour le statut"
    
    def mark_for_enrichment(self, request, queryset):
        count = queryset.update(needs_enrichment=True)
        self.message_user(request, f'{count} certificats marqués pour enrichissement')
    mark_for_enrichment.short_description = "Marquer pour enrichissement"
