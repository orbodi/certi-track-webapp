"""
Service d'analyse CSV pour la détection intelligente des certificats
"""
from datetime import datetime
from typing import Dict, List, Tuple
from .models import Certificate


class CSVAnalyzer:
    """
    Analyse les certificats du CSV et les compare avec la base de données
    pour détecter: nouveaux, mises à jour, doublons exacts, conflits
    """
    
    ACTION_NEW = 'new'
    ACTION_UPDATE = 'update'
    ACTION_DUPLICATE = 'duplicate'
    ACTION_CONFLICT = 'conflict'
    
    def __init__(self):
        self.existing_certs = {}
        self._load_existing_certificates()
    
    def _load_existing_certificates(self):
        """
        Charge tous les certificats actifs (non archivés) de la base
        Clé: common_name -> liste de certificats
        """
        active_certs = Certificate.objects.filter(archived=False).select_related()
        
        for cert in active_certs:
            if cert.common_name not in self.existing_certs:
                self.existing_certs[cert.common_name] = []
            
            # Normaliser valid_until en date (pas datetime) pour comparaison
            valid_until = cert.valid_until
            if hasattr(valid_until, 'date'):
                valid_until = valid_until.date()
            
            self.existing_certs[cert.common_name].append({
                'id': cert.id,
                'common_name': cert.common_name,
                'issuer': cert.issuer,
                'valid_until': valid_until,
                'template_name': cert.template_name,
                'environment': cert.environment,
                'created_at': cert.created_at,
            })
    
    def analyze_certificate(self, csv_cert: Dict) -> Dict:
        """
        Analyse un certificat du CSV et détermine l'action à effectuer
        
        Returns:
            {
                'csv_data': {...},          # Données du CSV
                'action': 'new|update|duplicate|conflict',
                'existing_cert': {...},      # Certificat existant (si applicable)
                'reason': 'Explication',
                'recommendation': 'Ce qui sera fait'
            }
        """
        common_name = csv_cert.get('common_name')
        csv_date = csv_cert.get('valid_until')
        
        # Normaliser la date du CSV en date (pas datetime)
        if csv_date and hasattr(csv_date, 'date'):
            csv_date = csv_date.date()
        
        # Certificat n'existe pas du tout
        if common_name not in self.existing_certs:
            return {
                'csv_data': csv_cert,
                'action': self.ACTION_NEW,
                'existing_cert': None,
                'reason': 'Certificat non présent dans la base',
                'recommendation': 'Sera créé'
            }
        
        # Certificat(s) existant(s) avec le même common_name
        existing_versions = self.existing_certs[common_name]
        
        # Chercher un doublon exact (même date d'expiration)
        exact_match = None
        for existing in existing_versions:
            if existing['valid_until'] == csv_date:
                exact_match = existing
                break
        
        # Doublon exact trouvé
        if exact_match:
            return {
                'csv_data': csv_cert,
                'action': self.ACTION_DUPLICATE,
                'existing_cert': exact_match,
                'reason': 'Certificat identique déjà présent (même date)',
                'recommendation': 'Sera ignoré'
            }
        
        # Trouver le certificat avec la date la plus récente
        most_recent = max(existing_versions, key=lambda x: x['valid_until'])
        
        # Cas 1: CSV contient une version plus récente (mise à jour)
        if csv_date > most_recent['valid_until']:
            return {
                'csv_data': csv_cert,
                'action': self.ACTION_UPDATE,
                'existing_cert': most_recent,
                'reason': f'Date plus récente ({csv_date.strftime("%d/%m/%Y")} > {most_recent["valid_until"].strftime("%d/%m/%Y")})',
                'recommendation': 'Ancien certificat sera archivé, nouveau sera créé'
            }
        
        # Cas 2: CSV contient une version plus ancienne (conflit)
        else:
            return {
                'csv_data': csv_cert,
                'action': self.ACTION_CONFLICT,
                'existing_cert': most_recent,
                'reason': f'Date antérieure ({csv_date.strftime("%d/%m/%Y")} < {most_recent["valid_until"].strftime("%d/%m/%Y")})',
                'recommendation': 'Nécessite décision manuelle'
            }
    
    def analyze_batch(self, csv_certificates: List[Dict]) -> Dict:
        """
        Analyse un lot de certificats du CSV
        
        Returns:
            {
                'results': [analyse par certificat],
                'summary': {
                    'new_count': X,
                    'update_count': Y,
                    'duplicate_count': Z,
                    'conflict_count': W,
                    'total': N
                }
            }
        """
        results = []
        summary = {
            'new_count': 0,
            'update_count': 0,
            'duplicate_count': 0,
            'conflict_count': 0,
            'error_count': 0,
            'total': len(csv_certificates)
        }
        
        for cert_data in csv_certificates:
            # Ignorer les lignes avec erreurs
            if 'error' in cert_data:
                summary['error_count'] += 1
                results.append({
                    'csv_data': cert_data,
                    'action': 'error',
                    'existing_cert': None,
                    'reason': cert_data.get('error'),
                    'recommendation': 'Sera ignoré'
                })
                continue
            
            # Analyser le certificat
            analysis = self.analyze_certificate(cert_data)
            results.append(analysis)
            
            # Mettre à jour les compteurs
            if analysis['action'] == self.ACTION_NEW:
                summary['new_count'] += 1
            elif analysis['action'] == self.ACTION_UPDATE:
                summary['update_count'] += 1
            elif analysis['action'] == self.ACTION_DUPLICATE:
                summary['duplicate_count'] += 1
            elif analysis['action'] == self.ACTION_CONFLICT:
                summary['conflict_count'] += 1
        
        return {
            'results': results,
            'summary': summary
        }
    
    def get_action_badge_class(self, action: str) -> str:
        """Retourne la classe CSS Bootstrap pour le badge d'action"""
        return {
            self.ACTION_NEW: 'bg-success',
            self.ACTION_UPDATE: 'bg-primary',
            self.ACTION_DUPLICATE: 'bg-secondary',
            self.ACTION_CONFLICT: 'bg-warning text-dark',
            'error': 'bg-danger'
        }.get(action, 'bg-light')
    
    def get_action_icon(self, action: str) -> str:
        """Retourne l'icône Bootstrap pour l'action"""
        return {
            self.ACTION_NEW: 'bi-plus-circle',
            self.ACTION_UPDATE: 'bi-arrow-repeat',
            self.ACTION_DUPLICATE: 'bi-dash-circle',
            self.ACTION_CONFLICT: 'bi-exclamation-triangle',
            'error': 'bi-x-circle'
        }.get(action, 'bi-question-circle')
    
    def get_action_label(self, action: str) -> str:
        """Retourne le libellé de l'action"""
        return {
            self.ACTION_NEW: 'Nouveau',
            self.ACTION_UPDATE: 'Mise à jour',
            self.ACTION_DUPLICATE: 'Doublon',
            self.ACTION_CONFLICT: 'Conflit',
            'error': 'Erreur'
        }.get(action, 'Inconnu')

