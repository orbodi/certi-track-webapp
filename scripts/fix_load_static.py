#!/usr/bin/env python3
"""
Script pour ajouter {% load static %} dans tous les templates qui utilisent {% static %}
mais qui n'ont pas le tag load.
"""

import os
import re
from pathlib import Path

def check_and_fix_template(file_path):
    """
    Vérifie si un template utilise {% static %} sans {% load static %}
    et l'ajoute si nécessaire
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si le template utilise {% static %}
    uses_static = bool(re.search(r'\{%\s*static\s+', content))
    
    # Vérifier si le template charge déjà static
    has_load_static = bool(re.search(r'\{%\s*load\s+static\s*%\}', content))
    
    if uses_static and not has_load_static:
        print(f"⚠️  Fichier sans {'{%'} load static {'%}'}: {file_path}")
        
        # Ajouter {% load static %} après {% extends %} ou au début
        if re.search(r'\{%\s*extends\s+', content):
            # Ajouter après {% extends %}
            content = re.sub(
                r'(\{%\s*extends\s+["\'][^"\']+["\']\s*%\})\s*\n',
                r'\1\n{% load static %}\n',
                content,
                count=1
            )
        else:
            # Ajouter au début du fichier
            if not content.startswith('{% load static %}'):
                content = '{% load static %}\n' + content
        
        # Écrire le fichier modifié
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ {'{%'} load static {'%}'} ajouté")
        return True
    
    elif uses_static and has_load_static:
        print(f"✅ OK: {file_path}")
    
    return False

def main():
    """
    Parcourt tous les templates et corrige ceux qui ont besoin de {% load static %}
    """
    print("🔍 Vérification de tous les templates...")
    print("=" * 70)
    
    templates_dir = Path('templates')
    if not templates_dir.exists():
        print("❌ Dossier templates/ introuvable")
        return
    
    fixed_count = 0
    total_count = 0
    
    # Parcourir tous les fichiers .html
    for html_file in templates_dir.rglob('*.html'):
        total_count += 1
        if check_and_fix_template(html_file):
            fixed_count += 1
    
    print("=" * 70)
    print(f"\n📊 Résumé:")
    print(f"   Total de fichiers vérifiés: {total_count}")
    print(f"   Fichiers corrigés: {fixed_count}")
    
    if fixed_count > 0:
        print(f"\n✅ {fixed_count} fichier(s) corrigé(s)")
    else:
        print(f"\n✅ Tous les templates sont OK!")

if __name__ == '__main__':
    main()

