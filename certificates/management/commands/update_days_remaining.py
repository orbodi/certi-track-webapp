"""
Commande pour mettre à jour le champ days_remaining de tous les certificats
Usage: python manage.py update_days_remaining
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from certificates.models import Certificate


class Command(BaseCommand):
    help = 'Met à jour le champ days_remaining pour tous les certificats'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche les détails pour chaque certificat',
        )
    
    def handle(self, *args, **options):
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('🔄 Mise à jour des jours restants...'))
        
        certificates = Certificate.objects.all()
        total = certificates.count()
        updated = 0
        
        for cert in certificates:
            old_days = cert.days_remaining
            
            # Le save() va calculer automatiquement days_remaining
            cert.save()
            
            if verbose:
                new_days = cert.days_remaining
                if old_days != new_days:
                    self.stdout.write(
                        f'  ✓ {cert.common_name}: {old_days} → {new_days} jours'
                    )
                else:
                    self.stdout.write(
                        f'  - {cert.common_name}: {new_days} jours (inchangé)'
                    )
            
            updated += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ {updated}/{total} certificat(s) mis à jour avec succès'
        ))

