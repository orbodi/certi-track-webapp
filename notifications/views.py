from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse

from .models import NotificationRule, NotificationLog, EmailSettings
from .forms import NotificationRuleForm, EmailSettingsForm


class NotificationRuleListView(LoginRequiredMixin, ListView):
    """Liste des règles de notification"""
    model = NotificationRule
    template_name = 'notifications/rule_list.html'
    context_object_name = 'rules'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['email_settings'] = EmailSettings.get_settings()
        
        # Statistiques
        context['stats'] = {
            'total_rules': NotificationRule.objects.count(),
            'active_rules': NotificationRule.objects.filter(is_active=True).count(),
            'total_sent': NotificationLog.objects.filter(status='sent').count(),
            'total_failed': NotificationLog.objects.filter(status='failed').count(),
        }
        
        return context


class NotificationRuleCreateView(LoginRequiredMixin, CreateView):
    """Créer une règle de notification"""
    model = NotificationRule
    form_class = NotificationRuleForm
    template_name = 'notifications/rule_form.html'
    success_url = reverse_lazy('notifications:rule_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Regle de notification creee avec succes!')
        return super().form_valid(form)


class NotificationRuleUpdateView(LoginRequiredMixin, UpdateView):
    """Modifier une règle de notification"""
    model = NotificationRule
    form_class = NotificationRuleForm
    template_name = 'notifications/rule_form.html'
    success_url = reverse_lazy('notifications:rule_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Regle modifiee avec succes!')
        return super().form_valid(form)


class NotificationRuleDeleteView(LoginRequiredMixin, DeleteView):
    """Supprimer une règle de notification"""
    model = NotificationRule
    template_name = 'notifications/rule_confirm_delete.html'
    success_url = reverse_lazy('notifications:rule_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Regle supprimee avec succes!')
        return super().delete(request, *args, **kwargs)


class NotificationLogListView(LoginRequiredMixin, ListView):
    """Journal des notifications"""
    model = NotificationLog
    template_name = 'notifications/log_list.html'
    context_object_name = 'logs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = NotificationLog.objects.select_related('certificate', 'rule')
        
        # Filtres
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        notification_type = self.request.GET.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        return queryset


@login_required
def email_settings_view(request):
    """Configuration globale des emails"""
    email_settings = EmailSettings.get_settings()
    
    if request.method == 'POST':
        form = EmailSettingsForm(request.POST, instance=email_settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuration email mise a jour avec succes!')
            return redirect('notifications:email_settings')
    else:
        form = EmailSettingsForm(instance=email_settings)
    
    return render(request, 'notifications/email_settings.html', {
        'form': form,
        'email_settings': email_settings
    })


@login_required
def test_email_view(request):
    """Tester l'envoi d'email"""
    if request.method == 'POST':
        email_settings = EmailSettings.get_settings()
        recipient = request.POST.get('recipient')
        
        try:
            # Import standard Python
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from django.template.loader import render_to_string
            
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['From'] = f'{email_settings.from_name} <{email_settings.from_email}>'
            msg['To'] = recipient
            msg['Subject'] = 'Test CertiTrack - Configuration Email'
            
            # Corps texte
            body_text = f'''Bonjour,

Ceci est un email de test pour verifier la configuration de CertiTrack.

Si vous recevez cet email, la configuration SMTP est correcte !

Configuration utilisee :
- Serveur : {email_settings.smtp_host}:{email_settings.smtp_port}
- TLS : {"Oui" if email_settings.smtp_use_tls else "Non"}
- SSL : {"Oui" if email_settings.smtp_use_ssl else "Non"}
- Utilisateur : {email_settings.smtp_username}

Date : {timezone.now().strftime("%d/%m/%Y %H:%M")}

---
CertiTrack - Gestion des Certificats SSL/TLS'''
            
            # Corps HTML
            base_url = request.build_absolute_uri('/')[:-1]
            context = {
                'email_settings': email_settings,
                'current_date': timezone.now(),
                'base_url': base_url,
            }
            body_html = render_to_string('emails/test_email.html', context)
            
            # Attacher les deux versions
            part1 = MIMEText(body_text, 'plain', 'utf-8')
            part2 = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)
            
            # Connexion SMTP
            if email_settings.smtp_use_ssl:
                server = smtplib.SMTP_SSL(
                    email_settings.smtp_host, 
                    email_settings.smtp_port,
                    timeout=email_settings.smtp_timeout
                )
            else:
                server = smtplib.SMTP(
                    email_settings.smtp_host, 
                    email_settings.smtp_port,
                    timeout=email_settings.smtp_timeout
                )
                if email_settings.smtp_use_tls:
                    server.starttls()
            
            # Authentification
            if email_settings.smtp_username and email_settings.smtp_password:
                server.login(email_settings.smtp_username, email_settings.smtp_password)
            
            # Envoi
            server.send_message(msg)
            server.quit()
            
            # Message de succès - ASCII pur
            messages.success(request, 'Email test envoye avec succes')
            
        except Exception as e:
            # Ne pas afficher le message d'erreur complet - juste un code
            messages.error(request, 'Erreur SMTP - Voir details dans le terminal')
            # Logger dans la console pour debug
            print(f"[ERROR] Test email failed: {repr(e)}")
    
    return redirect('notifications:email_settings')


@login_required
def dashboard_view(request):
    """Dashboard des notifications"""
    from certificates.models import Certificate
    from datetime import timedelta
    
    # Certificats expirant bientôt
    expiring_certs = Certificate.objects.filter(
        status='expiring_soon'
    ).order_by('valid_until')[:10]
    
    # Certificats expirés
    expired_certs = Certificate.objects.filter(
        status='expired'
    ).order_by('-valid_until')[:5]
    
    # Statistiques notifications
    logs_stats = {
        'today_sent': NotificationLog.objects.filter(
            sent_at__date=timezone.now().date(),
            status='sent'
        ).count(),
        'week_sent': NotificationLog.objects.filter(
            sent_at__gte=timezone.now() - timedelta(days=7),
            status='sent'
        ).count(),
        'total_failed': NotificationLog.objects.filter(status='failed').count(),
    }
    
    # Règles actives
    active_rules = NotificationRule.objects.filter(is_active=True)
    
    context = {
        'expiring_certs': expiring_certs,
        'expired_certs': expired_certs,
        'logs_stats': logs_stats,
        'active_rules': active_rules,
        'email_settings': EmailSettings.get_settings(),
    }
    
    return render(request, 'notifications/dashboard.html', context)


@login_required
def celery_schedules_view(request):
    """Vue pour gérer les horaires des tâches Celery"""
    from django_celery_beat.models import PeriodicTask, CrontabSchedule
    
    # Récupérer toutes les tâches périodiques
    tasks = PeriodicTask.objects.all().select_related('crontab')
    
    context = {
        'tasks': tasks,
        'email_settings': EmailSettings.get_settings(),
        'now': timezone.now(),
    }
    
    return render(request, 'notifications/celery_schedules.html', context)


@login_required
def celery_schedule_update(request, task_id):
    """Mettre à jour l'horaire d'une tâche Celery"""
    from django_celery_beat.models import PeriodicTask, CrontabSchedule
    
    task = get_object_or_404(PeriodicTask, pk=task_id)
    
    if request.method == 'POST':
        try:
            hour = int(request.POST.get('hour', 0))
            minute = int(request.POST.get('minute', 0))
            day_of_week = request.POST.get('day_of_week', '*')
            enabled = request.POST.get('enabled') == 'on'
            
            # Validation
            if not (0 <= hour <= 23):
                messages.error(request, 'L\'heure doit être entre 0 et 23')
                return redirect('notifications:celery_schedules')
            
            if not (0 <= minute <= 59):
                messages.error(request, 'Les minutes doivent être entre 0 et 59')
                return redirect('notifications:celery_schedules')
            
            # Créer ou récupérer la planification crontab
            schedule, created = CrontabSchedule.objects.get_or_create(
                minute=str(minute),
                hour=str(hour),
                day_of_week=day_of_week,
                day_of_month='*',
                month_of_year='*',
                timezone='UTC'
            )
            
            # Mettre à jour la tâche
            task.crontab = schedule
            task.enabled = enabled
            task.save()
            
            messages.success(
                request, 
                f'Tâche "{task.name}" mise à jour: {hour:02d}:{minute:02d} UTC, '
                f'{"Activée" if enabled else "Désactivée"}'
            )
            
        except ValueError as e:
            messages.error(request, f'Erreur de validation: {str(e)}')
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour: {str(e)}')
    
    return redirect('notifications:celery_schedules')


@login_required
def celery_task_create(request):
    """Créer une nouvelle tâche Celery planifiée"""
    from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
    from .forms import CeleryTaskForm
    import json
    
    if request.method == 'POST':
        form = CeleryTaskForm(request.POST)
        if form.is_valid():
            try:
                data = form.cleaned_data
                
                # Créer la planification selon le type
                if data['schedule_type'] == 'crontab':
                    schedule, _ = CrontabSchedule.objects.get_or_create(
                        minute=data['crontab_minute'],
                        hour=data['crontab_hour'],
                        day_of_week=data['crontab_day_of_week'],
                        day_of_month=data['crontab_day_of_month'],
                        month_of_year=data['crontab_month_of_year'],
                        timezone='UTC'
                    )
                    
                    # Créer la tâche
                    task = PeriodicTask.objects.create(
                        name=data['name'],
                        task=data['task'],
                        crontab=schedule,
                        enabled=data['enabled'],
                        one_off=data['one_off'],
                        description=data.get('description', ''),
                        args=data.get('args', '[]'),
                        kwargs=data.get('kwargs', '{}')
                    )
                else:
                    # Intervalle
                    schedule, _ = IntervalSchedule.objects.get_or_create(
                        every=data['interval_every'],
                        period=data['interval_period']
                    )
                    
                    task = PeriodicTask.objects.create(
                        name=data['name'],
                        task=data['task'],
                        interval=schedule,
                        enabled=data['enabled'],
                        one_off=data['one_off'],
                        description=data.get('description', ''),
                        args=data.get('args', '[]'),
                        kwargs=data.get('kwargs', '{}')
                    )
                
                messages.success(request, f'Tâche "{task.name}" créée avec succès')
                return redirect('notifications:celery_schedules')
                
            except Exception as e:
                messages.error(request, f'Erreur lors de la création: {str(e)}')
    else:
        form = CeleryTaskForm()
    
    context = {
        'form': form,
        'title': 'Créer une tâche planifiée',
        'action': 'create'
    }
    return render(request, 'notifications/celery_task_form.html', context)


@login_required
def celery_task_edit(request, task_id):
    """Modifier une tâche Celery existante"""
    from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
    from .forms import CeleryTaskForm
    import json
    
    task = get_object_or_404(PeriodicTask, pk=task_id)
    
    if request.method == 'POST':
        form = CeleryTaskForm(request.POST)
        if form.is_valid():
            try:
                data = form.cleaned_data
                
                # Mettre à jour les champs de base
                task.name = data['name']
                task.task = data['task']
                task.enabled = data['enabled']
                task.one_off = data['one_off']
                task.description = data.get('description', '')
                task.args = data.get('args', '[]')
                task.kwargs = data.get('kwargs', '{}')
                
                # Mettre à jour la planification
                if data['schedule_type'] == 'crontab':
                    schedule, _ = CrontabSchedule.objects.get_or_create(
                        minute=data['crontab_minute'],
                        hour=data['crontab_hour'],
                        day_of_week=data['crontab_day_of_week'],
                        day_of_month=data['crontab_day_of_month'],
                        month_of_year=data['crontab_month_of_year'],
                        timezone='UTC'
                    )
                    task.crontab = schedule
                    task.interval = None
                else:
                    schedule, _ = IntervalSchedule.objects.get_or_create(
                        every=data['interval_every'],
                        period=data['interval_period']
                    )
                    task.interval = schedule
                    task.crontab = None
                
                task.save()
                
                messages.success(request, f'Tâche "{task.name}" modifiée avec succès')
                return redirect('notifications:celery_schedules')
                
            except Exception as e:
                messages.error(request, f'Erreur lors de la modification: {str(e)}')
    else:
        # Pré-remplir le formulaire avec les données existantes
        initial_data = {
            'name': task.name,
            'task': task.task,
            'description': task.description,
            'enabled': task.enabled,
            'one_off': task.one_off,
            'args': task.args,
            'kwargs': task.kwargs,
        }
        
        if task.crontab:
            initial_data.update({
                'schedule_type': 'crontab',
                'crontab_minute': task.crontab.minute,
                'crontab_hour': task.crontab.hour,
                'crontab_day_of_week': task.crontab.day_of_week,
                'crontab_day_of_month': task.crontab.day_of_month,
                'crontab_month_of_year': task.crontab.month_of_year,
            })
        elif task.interval:
            initial_data.update({
                'schedule_type': 'interval',
                'interval_every': task.interval.every,
                'interval_period': task.interval.period,
            })
        
        form = CeleryTaskForm(initial=initial_data)
    
    context = {
        'form': form,
        'task': task,
        'title': f'Modifier: {task.name}',
        'action': 'edit'
    }
    return render(request, 'notifications/celery_task_form.html', context)


@login_required
def celery_task_delete(request, task_id):
    """Supprimer une tâche Celery"""
    from django_celery_beat.models import PeriodicTask
    
    task = get_object_or_404(PeriodicTask, pk=task_id)
    
    if request.method == 'POST':
        task_name = task.name
        task.delete()
        messages.success(request, f'Tâche "{task_name}" supprimée avec succès')
        return redirect('notifications:celery_schedules')
    
    context = {
        'task': task
    }
    return render(request, 'notifications/celery_task_confirm_delete.html', context)


@login_required
def celery_task_toggle(request, task_id):
    """Activer/Désactiver rapidement une tâche Celery"""
    from django_celery_beat.models import PeriodicTask
    
    task = get_object_or_404(PeriodicTask, pk=task_id)
    task.enabled = not task.enabled
    task.save()
    
    status = "activée" if task.enabled else "désactivée"
    messages.success(request, f'Tâche "{task.name}" {status}')
    
    return redirect('notifications:celery_schedules')
