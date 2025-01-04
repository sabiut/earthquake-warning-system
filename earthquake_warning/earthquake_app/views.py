from django.views.generic import TemplateView
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg
from .models import Earthquake
import json

class DashboardView(TemplateView):
    template_name = 'earthquake_app/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get earthquakes ordered by time
        earthquakes = Earthquake.objects.order_by('-time')[:50]
        
        # Prepare earthquake data for the map
        earthquake_data = []
        for eq in earthquakes:
            earthquake_data.append({
                'latitude': eq.latitude,
                'longitude': eq.longitude,
                'magnitude': eq.magnitude,
                'depth': eq.depth,
                'place': eq.place,
                'time': eq.time.isoformat(),
                'status': eq.status,
                'id': eq.id
            })

              # ✅ DEBUGGING: Print earthquake data to check if it's correctly passed
        print("🔍 Debugging: Earthquake Data (JSON format)")
        print(json.dumps(earthquake_data, indent=4))

        # Calculate statistics
        now = timezone.now()
        last_24h = now - timedelta(days=1)
        
        # Get earthquakes in the last 24 hours for stats
        recent_quakes = Earthquake.objects.filter(time__gte=last_24h)
        
        stats = {
            'total_24h': recent_quakes.count(),
            'avg_magnitude': round(recent_quakes.aggregate(Avg('magnitude'))['magnitude__avg'] or 0, 2),
            'active_alerts': recent_quakes.filter(status='alert').count(),
        }

        # Add to context
        context.update({
            'earthquakes': earthquakes,
            'earthquake_data': json.dumps(earthquake_data),
            'stats': stats,
            'last_update': now.isoformat(),
        })
        
        return context

def health_check(request):
    return JsonResponse({'status': 'ok'})

# Add this new view for real-time updates
def dashboard_data(request):
    earthquakes = Earthquake.objects.order_by('-time')[:50]
    now = timezone.now()
    last_24h = now - timedelta(days=1)
    recent_quakes = Earthquake.objects.filter(time__gte=last_24h)
    
    # Prepare earthquake data
    earthquake_data = [{
        'latitude': eq.latitude,
        'longitude': eq.longitude,
        'magnitude': eq.magnitude,
        'depth': eq.depth,
        'place': eq.place,
        'time': eq.time.isoformat(),
        'status': eq.status,
        'id': eq.id
    } for eq in earthquakes]
    
    # Prepare stats
    stats = {
        'total_24h': recent_quakes.count(),
        'avg_magnitude': round(recent_quakes.aggregate(Avg('magnitude'))['magnitude__avg'] or 0, 2),
        'active_alerts': recent_quakes.filter(status='alert').count(),
    }
    
    return JsonResponse({
        'earthquakes': earthquake_data,
        'stats': stats,
        'last_update': now.isoformat()
    })