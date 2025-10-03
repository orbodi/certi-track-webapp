from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone

from .models import Certificate
from .forms import ManualCertificateForm, CSVImportForm, DomainScanForm, BulkScanForm
from .utils import CertificateScanner


class CertificateListView(LoginRequiredMixin, ListView):
    model = Certificate
    template_name = 'certificates/certificate_list.html'
    context_object_name = 'certificates'
    paginate_by = 20
    
    def get_paginate_by(self, queryset):
        """Gérer le nombre d'éléments par page"""
        return self.request.GET.get('per_page', self.paginate_by)
    
    def get_queryset(self):
        queryset = Certificate.objects.all()
        
        # Filtre par statut
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filtre par environnement
        environment = self.request.GET.get('environment')
        if environment:
            queryset = queryset.filter(environment=environment)
        
        # Filtre par émetteur
        issuer = self.request.GET.get('issuer')
        if issuer:
            queryset = queryset.filter(issuer__icontains=issuer)
        
        # Filtre par jours restants (utilise le champ DB pour performance)
        days = self.request.GET.get('days')
        if days:
            try:
                if days == 'expired':
                    queryset = queryset.filter(days_remaining__lt=0)
                elif days == 'critical':
                    queryset = queryset.filter(days_remaining__gte=0, days_remaining__lte=7)
                elif days == 'warning':
                    queryset = queryset.filter(days_remaining__gt=7, days_remaining__lte=30)
                elif days == 'safe':
                    queryset = queryset.filter(days_remaining__gt=30)
                else:
                    days_int = int(days)
                    queryset = queryset.filter(days_remaining=days_int)
            except ValueError:
                pass
        
        # Filtre par date d'expiration
        expiration_date = self.request.GET.get('expiration_date')
        if expiration_date:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(expiration_date, '%Y-%m-%d').date()
                queryset = queryset.filter(valid_until=date_obj)
            except ValueError:
                pass
        
        # Filtre par période d'expiration
        expiration_period = self.request.GET.get('expiration_period')
        if expiration_period:
            today = timezone.now().date()
            if expiration_period == 'today':
                queryset = queryset.filter(valid_until=today)
            elif expiration_period == 'week':
                from datetime import timedelta
                week_end = today + timedelta(days=7)
                queryset = queryset.filter(valid_until__range=[today, week_end])
            elif expiration_period == 'month':
                from datetime import timedelta
                month_end = today + timedelta(days=30)
                queryset = queryset.filter(valid_until__range=[today, month_end])
            elif expiration_period == 'quarter':
                from datetime import timedelta
                quarter_end = today + timedelta(days=90)
                queryset = queryset.filter(valid_until__range=[today, quarter_end])
        
        # Recherche générale
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(common_name__icontains=search) | Q(issuer__icontains=search) | Q(template_name__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = {
            'total': Certificate.objects.count(),
            'active': Certificate.objects.filter(status='active').count(),
            'expiring_soon': Certificate.objects.filter(status='expiring_soon').count(),
            'expired': Certificate.objects.filter(status='expired').count(),
        }
        return context


class CertificateDetailView(LoginRequiredMixin, DetailView):
    model = Certificate
    template_name = 'certificates/certificate_detail.html'
    context_object_name = 'certificate'


class ManualCertificateCreateView(LoginRequiredMixin, CreateView):
    model = Certificate
    form_class = ManualCertificateForm
    template_name = 'certificates/certificate_form_manual.html'
    success_url = reverse_lazy('certificates:list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user if self.request.user.is_authenticated else None
        messages.success(self.request, f'Certificat {form.instance.common_name} créé!')
        return super().form_valid(form)


class CSVImportView(LoginRequiredMixin, FormView):
    template_name = 'certificates/certificate_import_csv.html'
    form_class = CSVImportForm
    success_url = reverse_lazy('certificates:list')
    
    def post(self, request, *args, **kwargs):
        # Si c'est une confirmation, ne pas valider le formulaire (pas de fichier)
        if 'confirm' in request.POST:
            return self.handle_confirmation()
        # Sinon, traiter normalement (preview)
        return super().post(request, *args, **kwargs)
    
    def handle_confirmation(self):
        """Gérer la confirmation de l'import depuis la session"""
        from datetime import datetime
        from django.utils import timezone as django_timezone
        from django.db import transaction
        
        certificates_data = self.request.session.get('csv_import_data', [])
        
        if not certificates_data:
            messages.error(self.request, 'Aucune donnée à importer. Veuillez recommencer l\'upload.')
            return redirect('certificates:import_csv')
        
        created_count, updated_count, error_count = 0, 0, 0
        
        # Utiliser une transaction atomique pour éviter les problèmes de lock SQLite
        with transaction.atomic():
            for cert_data in certificates_data:
                if 'error' in cert_data:
                    error_count += 1
                    continue
                
                try:
                    # Reconvertir la date ISO string en date (pas datetime)
                    valid_until = cert_data.get('valid_until')
                    if valid_until and isinstance(valid_until, str):
                        naive_dt = datetime.fromisoformat(valid_until)
                        # Convertir en date seulement (pas datetime)
                        valid_until = naive_dt.date()
                    
                    defaults = {
                        'issuer': cert_data.get('issuer', ''),
                        'valid_until': valid_until,
                        'key_usage': cert_data.get('key_usage'),
                        'friendly_name': cert_data.get('friendly_name'),
                        'template_name': cert_data.get('template_name'),
                        'environment': cert_data.get('environment'),
                        'import_method': 'csv',
                        'needs_enrichment': self.request.session.get('csv_auto_enrich', False),
                        'created_by': self.request.user if self.request.user.is_authenticated else None,
                    }
                    
                    # Créer un nouveau certificat sans vérifier les doublons
                    # Permet d'avoir plusieurs certificats avec le même nom mais des dates différentes
                    cert = Certificate.objects.create(
                        common_name=cert_data['common_name'],
                        **defaults
                    )
                    created = True
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                        
                except Exception as e:
                    error_count += 1
                    print(f"Erreur import CSV - {cert_data.get('common_name', 'Unknown')}: {str(e)}")
        
        # Nettoyer la session
        if 'csv_import_data' in self.request.session:
            del self.request.session['csv_import_data']
        if 'csv_auto_enrich' in self.request.session:
            del self.request.session['csv_auto_enrich']
        
        # Messages selon le résultat
        if error_count == len(certificates_data):
            messages.error(self.request, f'❌ Import échoué: {error_count} erreurs. Consultez les logs.')
        elif error_count > 0:
            messages.warning(self.request, f'⚠️ Import partiel: {created_count} créés, {updated_count} màj, {error_count} erreurs')
        else:
            messages.success(self.request, f'✅ Import réussi: {created_count} certificat(s) créé(s), {updated_count} mis à jour')
        
        return redirect(self.success_url)
    
    def form_valid(self, form):
        # Gérer uniquement le preview ici
        certificates_data = form.parse_csv()
        
        # Convertir les dates en chaînes pour la sérialisation JSON
        serializable_data = []
        for cert_data in certificates_data:
            serializable_cert = cert_data.copy()
            # Convertir datetime en ISO string
            if 'valid_until' in serializable_cert and serializable_cert['valid_until']:
                serializable_cert['valid_until'] = serializable_cert['valid_until'].isoformat()
            serializable_data.append(serializable_cert)
        
        # Stocker en session pour la confirmation
        self.request.session['csv_import_data'] = serializable_data
        self.request.session['csv_auto_enrich'] = form.cleaned_data.get('auto_enrich', False)
        
        return self.render_to_response(
            self.get_context_data(form=form, preview_data=certificates_data, preview_mode=True)
        )


class DomainScanView(LoginRequiredMixin, FormView):
    template_name = 'certificates/certificate_scan_domain.html'
    form_class = DomainScanForm
    success_url = reverse_lazy('certificates:list')
    
    def form_valid(self, form):
        scanner = CertificateScanner(
            timeout=form.cleaned_data['timeout'],
            verify_ssl=form.cleaned_data['verify_ssl']
        )
        result = scanner.scan_host(form.cleaned_data['hostname'], form.cleaned_data['port'])
        
        if not result.get('success'):
            messages.error(self.request, f"Échec: {result.get('error')}")
            return self.form_invalid(form)
        
        if 'preview' in self.request.POST:
            return self.render_to_response(
                self.get_context_data(form=form, scan_result=result, preview_mode=True)
            )
        
        if 'confirm' in self.request.POST:
            try:
                defaults = {
                    'issuer': result['issuer'],
                    'valid_from': result['valid_from'],
                    'valid_until': result['valid_until'],
                    'key_usage': result.get('key_usage'),
                    'san_list': result.get('san_list', []),
                    'serial_number': result['serial_number'],
                    'fingerprint_sha256': result['fingerprint_sha256'],
                    'signature_algorithm': result['signature_algorithm'],
                    'public_key_size': result.get('public_key_size'),
                    'pem_data': result.get('pem_data'),
                    'is_self_signed': result.get('is_self_signed', False),
                    'is_ca_certificate': result.get('is_ca_certificate', False),
                    'import_method': 'scan',
                    'scan_port': form.cleaned_data['port'],
                    'last_scanned': timezone.now(),
                    'environment': form.cleaned_data.get('environment'),
                    'notes': form.cleaned_data.get('notes'),
                    'created_by': self.request.user if self.request.user.is_authenticated else None,
                }
                
                cert, created = Certificate.objects.update_or_create(
                    common_name=result['common_name'], defaults=defaults
                )
                
                messages.success(self.request, f'Certificat {cert.common_name} {"créé" if created else "màj"}!')
                return redirect('certificates:detail', pk=cert.pk)
            except Exception as e:
                messages.error(self.request, f"Erreur: {e}")
                return self.form_invalid(form)
        
        return self.render_to_response(
            self.get_context_data(form=form, scan_result=result, preview_mode=True)
        )


class BulkScanView(LoginRequiredMixin, FormView):
    template_name = 'certificates/certificate_scan_bulk.html'
    form_class = BulkScanForm
    success_url = reverse_lazy('certificates:list')
    
    def form_valid(self, form):
        scanner = CertificateScanner(timeout=5, verify_ssl=False)
        results = scanner.scan_multiple_hosts(
            form.cleaned_data['hostnames'],
            form.cleaned_data['port']
        )
        
        if 'preview' in self.request.POST:
            return self.render_to_response(
                self.get_context_data(form=form, scan_results=results, preview_mode=True)
            )
        
        if 'confirm' in self.request.POST:
            created_count, updated_count, error_count = 0, 0, 0
            
            for result in results:
                if not result.get('success'):
                    error_count += 1
                    continue
                
                try:
                    defaults = {
                        'issuer': result['issuer'],
                        'valid_from': result['valid_from'],
                        'valid_until': result['valid_until'],
                        'key_usage': result.get('key_usage'),
                        'san_list': result.get('san_list', []),
                        'serial_number': result['serial_number'],
                        'fingerprint_sha256': result['fingerprint_sha256'],
                        'signature_algorithm': result['signature_algorithm'],
                        'public_key_size': result.get('public_key_size'),
                        'pem_data': result.get('pem_data'),
                        'is_self_signed': result.get('is_self_signed', False),
                        'is_ca_certificate': result.get('is_ca_certificate', False),
                        'import_method': 'scan',
                        'scan_port': form.cleaned_data['port'],
                        'last_scanned': timezone.now(),
                        'environment': form.cleaned_data.get('environment'),
                        'created_by': self.request.user if self.request.user.is_authenticated else None,
                    }
                    
                    cert, created = Certificate.objects.update_or_create(
                        common_name=result['common_name'], defaults=defaults
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                except:
                    error_count += 1
            
            messages.success(self.request, f'Scan: {created_count} créés, {updated_count} màj, {error_count} erreurs')
            return redirect(self.success_url)
        
        return self.render_to_response(
            self.get_context_data(form=form, scan_results=results, preview_mode=True)
        )


class ImportChoiceView(LoginRequiredMixin, TemplateView):
    template_name = 'certificates/import_choice.html'


class CertificateUpdateView(LoginRequiredMixin, UpdateView):
    model = Certificate
    form_class = ManualCertificateForm
    template_name = 'certificates/certificate_form_manual.html'
    
    def get_success_url(self):
        return reverse_lazy('certificates:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Certificat mis à jour!')
        return super().form_valid(form)


class CertificateDeleteView(LoginRequiredMixin, DeleteView):
    model = Certificate
    template_name = 'certificates/certificate_confirm_delete.html'
    success_url = reverse_lazy('certificates:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Certificat supprimé!')
        return super().delete(request, *args, **kwargs)

