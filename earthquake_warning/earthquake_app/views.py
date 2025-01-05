from django.views.generic import TemplateView
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Q
from django.core.cache import cache
from django.conf import settings
from .models import Earthquake
from .services import EarthquakeDataService
import logging
import json
from django.views.generic import ListView
from django.db import models 

logger = logging.getLogger(__name__)

class DashboardView(TemplateView):
    template_name = 'earthquake_app/dashboard.html'
    CACHE_TIMEOUT = getattr(settings, 'EARTHQUAKE_CACHE_TIMEOUT', 300)  # 5 minutes default

    def get_earthquake_data(self):
        """
        Fetch and format earthquake data with caching
        """
        cache_key = 'earthquake_data'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data

        try:
            earthquakes = Earthquake.objects.select_related().order_by('-time')[:50]
            
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

            cache.set(cache_key, earthquake_data, self.CACHE_TIMEOUT)
            return earthquake_data

        except Exception as e:
            logger.error(f"Error fetching earthquake data: {e}")
            return []

    def get_statistics(self):
        """
        Calculate and cache earthquake statistics
        """
        cache_key = 'earthquake_stats'
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            return cached_stats

        try:
            now = timezone.now()
            last_24h = now - timedelta(days=1)
            
            recent_quakes = Earthquake.objects.filter(
                time__gte=last_24h
            ).select_related()

            stats = {
                'total_24h': recent_quakes.count(),
                'avg_magnitude': round(
                    recent_quakes.aggregate(Avg('magnitude'))['magnitude__avg'] or 0, 
                    2
                ),
                'active_alerts': recent_quakes.filter(
                    Q(status='alert') | Q(magnitude__gte=4.5)
                ).count(),
                'highest_magnitude': recent_quakes.order_by('-magnitude').first().magnitude if recent_quakes else 0,
            }

            cache.set(cache_key, stats, self.CACHE_TIMEOUT)
            return stats

        except Exception as e:
            logger.error(f"Error calculating earthquake statistics: {e}")
            return {
                'total_24h': 0,
                'avg_magnitude': 0,
                'active_alerts': 0,
                'highest_magnitude': 0
            }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Fetch fresh data if needed
            EarthquakeDataService.fetch_recent_earthquakes()
            
            earthquake_data = self.get_earthquake_data()
            stats = self.get_statistics()

            if settings.DEBUG:
                logger.debug("Earthquake Data (JSON format)")
                logger.debug(json.dumps(earthquake_data, indent=4))

            context.update({
                'earthquakes': earthquake_data,
                'earthquake_data': json.dumps(earthquake_data),
                'stats': stats,
                'last_update': timezone.now().isoformat(),
                'error': None
            })

        except Exception as e:
            logger.error(f"Error in dashboard view: {e}")
            context.update({
                'error': 'Unable to load earthquake data. Please try again later.'
            })

        return context


def health_check(request):
    """
    Enhanced health check endpoint that verifies database connectivity
    """
    try:
        # Check database connection
        Earthquake.objects.first()
        
        # Check USGS API availability
        EarthquakeDataService.USGS_API_URL
        
        return JsonResponse({
            'status': 'ok',
            'timestamp': timezone.now().isoformat(),
            'database': 'connected',
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def dashboard_data(request):
    """
    API endpoint for real-time dashboard updates
    """
    try:
        # Attempt to fetch fresh data
        EarthquakeDataService.fetch_recent_earthquakes()
        
        dashboard_view = DashboardView()
        earthquake_data = dashboard_view.get_earthquake_data()
        stats = dashboard_view.get_statistics()

        return JsonResponse({
            'earthquakes': earthquake_data,
            'stats': stats,
            'last_update': timezone.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in dashboard data API: {e}")
        return JsonResponse({
            'error': 'Unable to fetch dashboard data',
            'detail': str(e)
        }, status=500)
    


class AlertsView(ListView):
    template_name = 'earthquake_app/alerts.html'
    context_object_name = 'alerts'
    
    def get_queryset(self):
        """
        Get earthquakes from the last 24 hours with magnitude >= 4.5
        or status='alert'
        """
        last_24h = timezone.now() - timedelta(days=1)
        return Earthquake.objects.filter(
            time__gte=last_24h
        ).filter(
            models.Q(magnitude__gte=4.5) | models.Q(status='alert')
        ).order_by('-magnitude', '-time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Earthquake Alerts'
        context['last_update'] = timezone.now().isoformat()
        return context