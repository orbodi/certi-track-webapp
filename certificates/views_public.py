from django.views.generic import TemplateView
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Certificate
from notifications.models import NotificationRule


class HomeView(TemplateView):
    """Page d'accueil publique"""
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques globales (publiques, sans détails)
        total = Certificate.objects.count()
        
        context['stats'] = {
            'total': total,
            'active': Certificate.objects.filter(status='active').count(),
            'expiring_soon': Certificate.objects.filter(status='expiring_soon').count(),
            'expired': Certificate.objects.filter(status='expired').count(),
        }
        
        # Informations système
        context['active_rules'] = NotificationRule.objects.filter(is_active=True).count()
        context['has_certificates'] = total > 0
        
        return context






