from django.shortcuts import render
from django.views.generic import TemplateView
from certificates.models import Certificate
from django.db.models import Count, Q
from django.utils import timezone


class WallDashboardView(TemplateView):
    """Dashboard pour affichage mural (wall display)"""
    template_name = 'dashboard/wall_display.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques globales
        all_certs = Certificate.objects.all()
        context['stats'] = {
            'total': all_certs.count(),
            'active': all_certs.filter(status='active').count(),
            'expiring_soon': all_certs.filter(status='expiring_soon').count(),
            'expired': all_certs.filter(status='expired').count(),
        }
        
        # Récupérer TOUS les certificats et les trier par urgence
        # Ordre de priorité : Critiques (<=7j) > Orange (8-30j) > Vert (>30j) > Expirés
        
        all_active_certs = Certificate.objects.exclude(
            days_remaining__isnull=True
        ).order_by('days_remaining')
        
        # Convertir en liste pour division en 2 colonnes
        all_certs_list = list(all_active_certs)
        
        # Remplir la colonne de gauche d'abord (max ~30 certificats par colonne)
        # Calculer dynamiquement selon le nombre de certificats
        max_per_column = 30
        
        if len(all_certs_list) <= max_per_column:
            # Tous dans la colonne 1
            context['column1_certs'] = all_certs_list
            context['column2_certs'] = []
        else:
            # Remplir colonne 1, puis le reste dans colonne 2
            context['column1_certs'] = all_certs_list[:max_per_column]
            context['column2_certs'] = all_certs_list[max_per_column:]
        
        # Catégoriser les certificats pour les 3 cartes
        context['critical_certs'] = [c for c in all_certs_list if c.days_remaining is not None and 0 <= c.days_remaining <= 7]
        context['warning_certs'] = [c for c in all_certs_list if c.days_remaining is not None and 7 < c.days_remaining <= 30]
        context['active_certs'] = [c for c in all_certs_list if c.days_remaining is not None and c.days_remaining > 30]
        context['expired_certs'] = [c for c in all_certs_list if c.days_remaining is not None and c.days_remaining < 0]
        
        # Statistiques par environnement
        context['env_stats'] = Certificate.objects.values('environment').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Heure actuelle
        context['current_time'] = timezone.now()
        
        # Auto-refresh en secondes (défaut: 60s)
        context['refresh_interval'] = self.request.GET.get('refresh', 60)
        
        return context
