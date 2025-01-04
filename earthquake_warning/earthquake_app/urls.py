from django.urls import path
from .views import DashboardView, health_check, dashboard_data  # Add dashboard_data import

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('health/', health_check, name='health_check'),
    path('api/dashboard-data/', dashboard_data, name='dashboard-data'),  # Add new endpoint
]