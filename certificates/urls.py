from django.urls import path
from . import views
from .views_public import HomeView

app_name = 'certificates'

urlpatterns = [
    # Page d'accueil
    path('home/', HomeView.as_view(), name='home'),
    
    # Liste et détail
    path('', views.CertificateListView.as_view(), name='list'),
    path('<int:pk>/', views.CertificateDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.CertificateUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.CertificateDeleteView.as_view(), name='delete'),
    
    # Import - Page de choix
    path('import/', views.ImportChoiceView.as_view(), name='import_choice'),
    
    # Méthode 1: Saisie manuelle
    path('import/manual/', views.ManualCertificateCreateView.as_view(), name='import_manual'),
    
    # Méthode 2: Import CSV
    path('import/csv/', views.CSVImportView.as_view(), name='import_csv'),
    
    # Méthode 3: Scan domaine
    path('import/scan/', views.DomainScanView.as_view(), name='import_scan'),
    path('import/scan/bulk/', views.BulkScanView.as_view(), name='import_scan_bulk'),
]

