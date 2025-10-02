"""
Utilitaires pour les notifications
"""
import unicodedata


def remove_accents(text):
    """
    Supprime les accents d'un texte
    """
    if not text:
        return text
    
    # Normaliser en NFD (décomposition)
    nfd = unicodedata.normalize('NFD', text)
    
    # Garder seulement les caractères ASCII
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')


def clean_for_ascii(text):
    """
    Nettoie un texte pour l'encodage ASCII
    Remplace les caractères spéciaux
    """
    if not text:
        return text
    
    # Remplacements spécifiques
    replacements = {
        'à': 'a', 'â': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'î': 'i', 'ï': 'i',
        'ô': 'o', 'ö': 'o',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c',
        ''': "'", ''': "'",
        '"': '"', '"': '"',
        '…': '...',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Supprimer les emojis et autres caractères non-ASCII
    try:
        text.encode('ascii')
        return text
    except UnicodeEncodeError:
        # Si ça échoue encore, forcer ASCII
        return text.encode('ascii', 'replace').decode('ascii').replace('?', '')


def safe_email_content(text):
    """
    Sécurise le contenu d'un email pour éviter les problèmes d'encodage
    """
    if isinstance(text, str):
        return clean_for_ascii(text)
    return text




