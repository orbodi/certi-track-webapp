from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),
    
    # Règles de notification
    path('rules/', views.NotificationRuleListView.as_view(), name='rule_list'),
    path('rules/create/', views.NotificationRuleCreateView.as_view(), name='rule_create'),
    path('rules/<int:pk>/edit/', views.NotificationRuleUpdateView.as_view(), name='rule_edit'),
    path('rules/<int:pk>/delete/', views.NotificationRuleDeleteView.as_view(), name='rule_delete'),
    
    # Journal des notifications
    path('logs/', views.NotificationLogListView.as_view(), name='log_list'),
    
    # Configuration email
    path('settings/', views.email_settings_view, name='email_settings'),
    path('settings/test-email/', views.test_email_view, name='test_email'),
    
    # Planification Celery
    path('schedules/', views.celery_schedules_view, name='celery_schedules'),
    path('schedules/<int:task_id>/update/', views.celery_schedule_update, name='celery_schedule_update'),
    path('schedules/create/', views.celery_task_create, name='celery_task_create'),
    path('schedules/<int:task_id>/edit/', views.celery_task_edit, name='celery_task_edit'),
    path('schedules/<int:task_id>/delete/', views.celery_task_delete, name='celery_task_delete'),
    path('schedules/<int:task_id>/toggle/', views.celery_task_toggle, name='celery_task_toggle'),
]




