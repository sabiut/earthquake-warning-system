from django.urls import path
from .views import PredictionsDashboardView

urlpatterns = [
    path('earthquakepredictions/', PredictionsDashboardView.as_view(), name='earthquakepredictions'),
]