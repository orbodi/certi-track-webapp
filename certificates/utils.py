"""
Utilitaires pour la gestion des certificats
"""
import ssl
import socket
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CertificateScanner:
    """
    Scanner pour récupérer les certificats SSL/TLS depuis les serveurs
    """
    
    def __init__(self, timeout: int = 5, verify_ssl: bool = False):
        self.timeout = timeout
        self.verify_ssl = verify_ssl
    
    def scan_host(self, hostname: str, port: int = 443) -> Dict:
        """
        Scanne un serveur et récupère son certificat
        
        Args:
            hostname: FQDN du serveur (ex: jenkins.eid.local)
            port: Port SSL/TLS (défaut: 443)
        
        Returns:
            Dict avec les informations du certificat ou une erreur
        """
        try:
            # Créer le contexte SSL
            context = ssl.create_default_context()
            
            if not self.verify_ssl:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            
            # Se connecter au serveur
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Récupérer le certificat
                    cert_bin = ssock.getpeercert(binary_form=True)
                    cert = x509.load_der_x509_certificate(cert_bin, default_backend())
                    
                    return self.parse_certificate(cert, hostname)
                    
        except socket.timeout:
            return {
                'success': False,
                'error': f'Timeout: impossible de se connecter à {hostname}:{port} dans les {self.timeout}s'
            }
        except socket.gaierror:
            return {
                'success': False,
                'error': f'Erreur DNS: impossible de résoudre {hostname}'
            }
        except ConnectionRefusedError:
            return {
                'success': False,
                'error': f'Connexion refusée sur {hostname}:{port}. Le port est-il ouvert?'
            }
        except ssl.SSLError as e:
            return {
                'success': False,
                'error': f'Erreur SSL: {str(e)}'
            }
        except Exception as e:
            logger.exception(f"Erreur lors du scan de {hostname}:{port}")
            return {
                'success': False,
                'error': f'Erreur inattendue: {str(e)}'
            }
    
    def parse_certificate(self, cert: x509.Certificate, hostname: str = None) -> Dict:
        """
        Parse un certificat x509 et extrait toutes les métadonnées
        
        Args:
            cert: Certificat x509
            hostname: Hostname scanné (optionnel)
        
        Returns:
            Dict avec toutes les informations du certificat
        """
        try:
            # Extraire le Common Name
            try:
                common_name = cert.subject.get_attributes_for_oid(
                    x509.NameOID.COMMON_NAME
                )[0].value
            except (IndexError, AttributeError):
                common_name = hostname or "Unknown"
            
            # Extraire l'Issuer
            try:
                issuer_cn = cert.issuer.get_attributes_for_oid(
                    x509.NameOID.COMMON_NAME
                )[0].value
            except (IndexError, AttributeError):
                issuer_cn = cert.issuer.rfc4514_string()
            
            # Extraire les SAN (Subject Alternative Names)
            san_list = []
            try:
                san_ext = cert.extensions.get_extension_for_oid(
                    x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
                )
                san_list = [str(name.value) for name in san_ext.value]
            except x509.ExtensionNotFound:
                pass
            
            # Vérifier si c'est un certificat auto-signé
            is_self_signed = cert.issuer == cert.subject
            
            # Vérifier si c'est un certificat CA
            is_ca = False
            try:
                basic_constraints = cert.extensions.get_extension_for_oid(
                    x509.ExtensionOID.BASIC_CONSTRAINTS
                )
                is_ca = basic_constraints.value.ca
            except x509.ExtensionNotFound:
                pass
            
            # Extraire Key Usage
            key_usage_list = []
            try:
                key_usage_ext = cert.extensions.get_extension_for_oid(
                    x509.ExtensionOID.KEY_USAGE
                )
                ku = key_usage_ext.value
                if ku.digital_signature:
                    key_usage_list.append("Signature numérique")
                if ku.key_encipherment:
                    key_usage_list.append("Chiffrement de clé")
                if ku.key_cert_sign:
                    key_usage_list.append("Signature de certificat")
            except (x509.ExtensionNotFound, AttributeError):
                pass
            
            # Extended Key Usage
            try:
                ext_key_usage = cert.extensions.get_extension_for_oid(
                    x509.ExtensionOID.EXTENDED_KEY_USAGE
                )
                for oid in ext_key_usage.value:
                    if oid == x509.ExtendedKeyUsageOID.SERVER_AUTH:
                        key_usage_list.append("Authentification du serveur")
                    elif oid == x509.ExtendedKeyUsageOID.CLIENT_AUTH:
                        key_usage_list.append("Authentification du client")
            except (x509.ExtensionNotFound, AttributeError):
                pass
            
            # Taille de la clé publique
            try:
                public_key_size = cert.public_key().key_size
            except AttributeError:
                public_key_size = None
            
            return {
                'success': True,
                'common_name': common_name,
                'issuer': issuer_cn,
                'issuer_full': cert.issuer.rfc4514_string(),
                'serial_number': format(cert.serial_number, 'X'),  # Format hexadécimal
                'valid_from': cert.not_valid_before_utc if hasattr(cert, 'not_valid_before_utc') else cert.not_valid_before,
                'valid_until': cert.not_valid_after_utc if hasattr(cert, 'not_valid_after_utc') else cert.not_valid_after,
                'san_list': san_list,
                'fingerprint_sha256': cert.fingerprint(hashes.SHA256()).hex().upper(),
                'signature_algorithm': cert.signature_algorithm_oid._name,
                'public_key_size': public_key_size,
                'public_key_type': type(cert.public_key()).__name__,
                'is_self_signed': is_self_signed,
                'is_ca_certificate': is_ca,
                'key_usage': ', '.join(key_usage_list) if key_usage_list else None,
                'pem_data': cert.public_bytes(
                    encoding=serialization.Encoding.PEM
                ).decode('utf-8'),
                'version': cert.version.name,
            }
            
        except Exception as e:
            logger.exception("Erreur lors du parsing du certificat")
            return {
                'success': False,
                'error': f'Erreur lors du parsing: {str(e)}'
            }
    
    def scan_multiple_hosts(self, hostnames: list, port: int = 443) -> list:
        """
        Scanne plusieurs serveurs
        
        Args:
            hostnames: Liste de FQDNs
            port: Port SSL/TLS
        
        Returns:
            Liste de dicts avec les résultats
        """
        results = []
        for hostname in hostnames:
            result = self.scan_host(hostname, port)
            result['hostname'] = hostname
            results.append(result)
        return results


def parse_csv_date(date_str: str) -> Optional[datetime]:
    """
    Parse une date depuis le format CSV
    Essaie plusieurs formats courants
    """
    if not date_str or date_str.strip() in ['', '<Aucun>']:
        return None
    
    date_str = date_str.strip()
    
    # Formats à essayer
    formats = [
        '%d/%m/%Y',           # 17/09/2025
        '%Y-%m-%d',           # 2025-09-17
        '%d/%m/%Y %H:%M',     # 17/09/2025 14:30
        '%Y-%m-%d %H:%M:%S',  # 2025-09-17 14:30:00
        '%d-%m-%Y',           # 17-09-2025
        '%m/%d/%Y',           # 09/17/2025 (format US)
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Si aucun format ne fonctionne
    logger.warning(f"Impossible de parser la date: {date_str}")
    return None


def clean_csv_value(value: str) -> Optional[str]:
    """
    Nettoie une valeur du CSV
    """
    if not value:
        return None
    
    value = value.strip()
    
    if value in ['<Aucun>', '', 'N/A', 'None', '-']:
        return None
    
    return value

