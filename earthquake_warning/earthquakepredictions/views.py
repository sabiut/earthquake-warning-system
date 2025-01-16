# views.py
from django.views.generic import TemplateView
from django.utils import timezone
from .services import prepare_earthquake_data
import json

class PredictionsDashboardView(TemplateView):
    template_name = 'predictions/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['predictions_json'] = prepare_earthquake_data()
            print("Predictions JSON prepared successfully")
        except Exception as e:
            print(f"Error preparing predictions JSON: {e}")
            context['predictions_json'] = json.dumps({'predictions': []})
        return context