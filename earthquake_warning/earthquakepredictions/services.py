# services.py
from django.core.serializers import serialize
from django.utils import timezone
from earthquake_app.models import Earthquake
import json

def prepare_earthquake_data():
    """Prepare earthquake predictions data for visualization"""
    predicted_quakes = Earthquake.objects.filter(
        status='predicted',
        time__gte=timezone.now(),
        time__lte=timezone.now() + timezone.timedelta(days=30)
    ).order_by('time')
    
    print(f"Found {predicted_quakes.count()} predicted earthquakes")
    
    predictions = json.loads(serialize('json', predicted_quakes))
    predictions = [
        {
            'id': p['pk'],
            'magnitude': float(p['fields']['magnitude']),
            'latitude': float(p['fields']['latitude']),
            'longitude': float(p['fields']['longitude']),
            'time': p['fields']['time'],
            'place': p['fields']['place'],
            'depth': float(p['fields']['depth']),
            'status': p['fields']['status']
        }
        for p in predictions
    ]
    
    # Debug print first few predictions
    if predictions:
        print("Sample prediction:", predictions[0])
    
    result = json.dumps({'predictions': predictions})
    print("JSON string length:", len(result))
    
    return result