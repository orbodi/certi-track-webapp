from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('wall/', views.WallDashboardView.as_view(), name='wall_display'),
]

