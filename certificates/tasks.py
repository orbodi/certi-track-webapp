"""
Tâches Celery pour les certificats
"""
from celery import shared_task
from django.utils import timezone

from .models import Certificate
from .utils import CertificateScanner


@shared_task(name='certificates.tasks.auto_scan_certificates')
def auto_scan_certificates():
    """
    Tâche Celery pour scanner automatiquement les certificats
    qui nécessitent un enrichissement
    """
    # Récupérer les certificats à enrichir
    certs_to_scan = Certificate.objects.filter(needs_enrichment=True)[:50]  # Max 50 par batch
    
    if not certs_to_scan.exists():
        return 'Aucun certificat à scanner'
    
    scanner = CertificateScanner(timeout=5, verify_ssl=False)
    success_count = 0
    error_count = 0
    
    for cert in certs_to_scan:
        try:
            result = scanner.scan_host(cert.common_name, cert.scan_port or 443)
            
            if result.get('success'):
                # Mettre à jour avec les données enrichies
                cert.valid_from = result.get('valid_from')
                cert.san_list = result.get('san_list', [])
                cert.serial_number = result.get('serial_number')
                cert.fingerprint_sha256 = result.get('fingerprint_sha256')
                cert.signature_algorithm = result.get('signature_algorithm')
                cert.public_key_size = result.get('public_key_size')
                cert.pem_data = result.get('pem_data')
                cert.is_self_signed = result.get('is_self_signed', False)
                cert.is_ca_certificate = result.get('is_ca_certificate', False)
                
                cert.needs_enrichment = False
                cert.last_scanned = timezone.now()
                cert.scan_error = None
                cert.save()
                
                success_count += 1
            else:
                cert.scan_error = result.get('error')
                cert.last_scanned = timezone.now()
                cert.save()
                error_count += 1
                
        except Exception as e:
            cert.scan_error = str(e)
            cert.last_scanned = timezone.now()
            cert.save()
            error_count += 1
    
    return f'Scan terminé: {success_count} succès, {error_count} erreurs'


@shared_task(name='certificates.tasks.scan_certificate_async')
def scan_certificate_async(certificate_id, port=443):
    """
    Tâche pour scanner un certificat de manière asynchrone
    """
    try:
        cert = Certificate.objects.get(id=certificate_id)
        scanner = CertificateScanner(timeout=5, verify_ssl=False)
        
        result = scanner.scan_host(cert.common_name, port)
        
        if result.get('success'):
            cert.valid_from = result.get('valid_from')
            cert.san_list = result.get('san_list', [])
            cert.serial_number = result.get('serial_number')
            cert.fingerprint_sha256 = result.get('fingerprint_sha256')
            cert.signature_algorithm = result.get('signature_algorithm')
            cert.public_key_size = result.get('public_key_size')
            cert.pem_data = result.get('pem_data')
            cert.is_self_signed = result.get('is_self_signed', False)
            cert.is_ca_certificate = result.get('is_ca_certificate', False)
            
            cert.needs_enrichment = False
            cert.last_scanned = timezone.now()
            cert.scan_error = None
            cert.save()
            
            return f'Certificat {cert.common_name} scanné avec succès'
        else:
            cert.scan_error = result.get('error')
            cert.last_scanned = timezone.now()
            cert.save()
            return f'Erreur: {result.get("error")}'
            
    except Certificate.DoesNotExist:
        return f'Certificat {certificate_id} introuvable'
    except Exception as e:
        return f'Erreur: {str(e)}'


@shared_task(name='certificates.tasks.update_days_remaining')
def update_days_remaining():
    """
    Tâche Celery pour mettre à jour le champ days_remaining de tous les certificats
    Exécutée quotidiennement pour garder les données à jour
    """
    from django.core.management import call_command
    
    try:
        call_command('update_days_remaining')
        return 'Mise à jour des jours restants terminée avec succès'
    except Exception as e:
        return f'Erreur lors de la mise à jour: {str(e)}'
