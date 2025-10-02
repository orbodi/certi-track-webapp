from django import forms
from django.core.exceptions import ValidationError
from .models import Certificate
import csv
import io
from datetime import datetime


class ManualCertificateForm(forms.ModelForm):
    """
    Formulaire pour saisie manuelle d'un certificat
    Basé sur le format CSV (délivré à, délivré par, date expiration, etc.)
    """
    
    valid_until = forms.DateTimeField(
        label="Date d'expiration",
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        }),
        input_formats=['%Y-%m-%dT%H:%M', '%d/%m/%Y', '%Y-%m-%d'],
        help_text="Format: JJ/MM/AAAA ou sélectionnez avec le calendrier"
    )
    
    class Meta:
        model = Certificate
        fields = [
            'common_name',
            'issuer',
            'valid_until',
            'key_usage',
            'friendly_name',
            'template_name',
            'environment',
            'notes',
        ]
        widgets = {
            'common_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: jenkins.eid.local'}),
            'issuer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: eid-CA-01-CA'}),
            'key_usage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Authentification du serveur'}),
            'friendly_name': forms.TextInput(attrs={'class': 'form-control'}),
            'template_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: CertSSLIdemia'}),
            'environment': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def save(self, commit=True):
        certificate = super().save(commit=False)
        certificate.import_method = 'manual'
        if commit:
            certificate.save()
        return certificate


class CSVImportForm(forms.Form):
    """
    Formulaire pour l'import CSV avec preview
    """
    
    csv_file = forms.FileField(
        label="Fichier CSV",
        help_text="Format: Délivré à | Délivré par | Date d'expiration | Rôles prévus | Nom convivial | Statut | Modèle de certificat",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.txt'
        })
    )
    
    skip_header = forms.BooleanField(
        label="Ignorer la première ligne (en-tête)",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    delimiter = forms.ChoiceField(
        label="Séparateur",
        choices=[
            ('\t', 'Tabulation'),
            (';', 'Point-virgule (;)'),
            (',', 'Virgule (,)'),
        ],
        initial='\t',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    auto_enrich = forms.BooleanField(
        label="Enrichir automatiquement (scanner les domaines après import)",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    default_environment = forms.ChoiceField(
        label="Environnement par défaut",
        choices=[('', '-- Non spécifié --')] + list(Certificate.ENVIRONMENT_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        
        # Vérifier la taille du fichier (max 5MB)
        if csv_file.size > 5 * 1024 * 1024:
            raise ValidationError("Le fichier est trop volumineux (max 5MB)")
        
        # Vérifier l'extension
        if not csv_file.name.endswith(('.csv', '.txt')):
            raise ValidationError("Format de fichier non supporté. Utilisez .csv ou .txt")
        
        return csv_file
    
    def parse_csv(self):
        """
        Parse le fichier CSV et retourne une liste de dictionnaires
        avec preview des données
        """
        csv_file = self.cleaned_data['csv_file']
        skip_header = self.cleaned_data['skip_header']
        delimiter = self.cleaned_data['delimiter']
        
        # Lire le contenu avec détection automatique de l'encodage
        csv_file.seek(0)
        raw_content = csv_file.read()
        
        # Essayer différents encodages courants
        encodings = ['utf-8-sig', 'utf-8', 'windows-1252', 'iso-8859-1', 'cp1252', 'latin-1']
        content = None
        
        for encoding in encodings:
            try:
                content = raw_content.decode(encoding)
                break
            except (UnicodeDecodeError, AttributeError):
                continue
        
        if content is None:
            raise ValidationError("Impossible de lire le fichier. Encodage non supporté.")
        
        # Parser le CSV
        reader = csv.reader(io.StringIO(content), delimiter=delimiter)
        
        certificates_data = []
        
        for i, row in enumerate(reader):
            # Ignorer l'en-tête si demandé
            if i == 0 and skip_header:
                continue
            
            # Ignorer les lignes vides
            if not row or all(cell.strip() == '' for cell in row):
                continue
            
            try:
                # Parser la date (format français JJ/MM/AAAA)
                date_str = row[2].strip() if len(row) > 2 else ''
                if date_str:
                    # Essayer différents formats
                    for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d/%m/%Y %H:%M', '%Y-%m-%d %H:%M:%S']:
                        try:
                            valid_until = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        valid_until = None
                else:
                    valid_until = None
                
                cert_data = {
                    'common_name': row[0].strip() if len(row) > 0 else '',
                    'issuer': row[1].strip() if len(row) > 1 else '',
                    'valid_until': valid_until,
                    'key_usage': row[3].strip() if len(row) > 3 and row[3].strip() != '<Aucun>' else None,
                    'friendly_name': row[4].strip() if len(row) > 4 and row[4].strip() != '<Aucun>' else None,
                    'status_csv': row[5].strip() if len(row) > 5 else '',
                    'template_name': row[6].strip() if len(row) > 6 else None,
                    'environment': self.cleaned_data.get('default_environment') or None,
                    'line_number': i + 1,
                }
                
                certificates_data.append(cert_data)
                
            except Exception as e:
                # Ajouter l'erreur aux données pour affichage
                certificates_data.append({
                    'error': f"Erreur ligne {i + 1}: {str(e)}",
                    'line_number': i + 1,
                    'raw_data': row,
                })
        
        return certificates_data


class DomainScanForm(forms.Form):
    """
    Formulaire pour scanner un domaine et récupérer automatiquement
    les informations du certificat
    """
    
    hostname = forms.CharField(
        label="Nom de domaine ou serveur",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: jenkins.eid.local ou gitlab.eid.local'
        }),
        help_text="FQDN du serveur à scanner"
    )
    
    port = forms.IntegerField(
        label="Port",
        initial=443,
        min_value=1,
        max_value=65535,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        }),
        help_text="Port SSL/TLS (443 par défaut)"
    )
    
    timeout = forms.IntegerField(
        label="Timeout (secondes)",
        initial=5,
        min_value=1,
        max_value=30,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        }),
        help_text="Délai d'attente pour la connexion"
    )
    
    verify_ssl = forms.BooleanField(
        label="Vérifier le certificat SSL",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Décochez pour accepter les certificats auto-signés"
    )
    
    environment = forms.ChoiceField(
        label="Environnement",
        choices=[('', '-- Sélectionner --')] + list(Certificate.ENVIRONMENT_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    notes = forms.CharField(
        label="Notes",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Notes optionnelles sur ce certificat...'
        })
    )
    
    def clean_hostname(self):
        hostname = self.cleaned_data['hostname'].strip()
        # Supprimer le protocole si présent
        hostname = hostname.replace('https://', '').replace('http://', '')
        # Supprimer le port si présent
        if ':' in hostname:
            hostname = hostname.split(':')[0]
        return hostname


class BulkScanForm(forms.Form):
    """
    Formulaire pour scanner plusieurs domaines à la fois
    """
    
    hostnames = forms.CharField(
        label="Liste de domaines",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Un domaine par ligne:\njenkins.eid.local\ngitlab.eid.local\njira-uat.eid.local'
        }),
        help_text="Un nom de domaine par ligne"
    )
    
    port = forms.IntegerField(
        label="Port par défaut",
        initial=443,
        min_value=1,
        max_value=65535,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    environment = forms.ChoiceField(
        label="Environnement par défaut",
        choices=[('', '-- Non spécifié --')] + list(Certificate.ENVIRONMENT_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def clean_hostnames(self):
        hostnames_text = self.cleaned_data['hostnames']
        hostnames = []
        
        for line in hostnames_text.strip().split('\n'):
            hostname = line.strip()
            if hostname and not hostname.startswith('#'):
                # Nettoyer le hostname
                hostname = hostname.replace('https://', '').replace('http://', '')
                if ':' in hostname:
                    hostname = hostname.split(':')[0]
                hostnames.append(hostname)
        
        if not hostnames:
            raise ValidationError("Veuillez entrer au moins un nom de domaine")
        
        if len(hostnames) > 50:
            raise ValidationError("Maximum 50 domaines à la fois")
        
        return hostnames

