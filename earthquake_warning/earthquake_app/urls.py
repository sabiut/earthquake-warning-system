from django.urls import path
from .views import DashboardView, health_check, dashboard_data, AlertsView,get_predicted_earthquakes

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('health/', health_check, name='health_check'),
    path('api/dashboard-data/', dashboard_data, name='dashboard-data'),  # Add new endpoint
    path('alerts/', AlertsView.as_view(), name='alerts'),
    path("api/predictions/", get_predicted_earthquakes, name="get_predicted_earthquakes"),
]