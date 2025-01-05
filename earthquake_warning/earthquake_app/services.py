# services.py
import requests
import logging
from django.utils import timezone
from django.db import transaction
from .models import Earthquake

logger = logging.getLogger(__name__)

class EarthquakeDataService:
    USGS_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    
    @classmethod
    def fetch_recent_earthquakes(cls):
        """
        Fetch and store earthquakes from USGS API from the last 24 hours.
        Implements error handling, data validation, and atomic transactions.
        """
        try:
            # Fetch data from USGS API
            response = requests.get(cls.USGS_API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'features' not in data:
                logger.error("Invalid API response: 'features' key missing")
                return
            
            twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
            latest_earthquakes = []
            
            # Process earthquake data
            for feature in data['features']:
                try:
                    properties = feature['properties']
                    geometry = feature['geometry']
                    
                    # Validate required fields
                    required_fields = {
                        'mag': properties.get('mag'),
                        'place': properties.get('place'),
                        'time': properties.get('time'),
                        'coordinates': geometry.get('coordinates')
                    }
                    
                    if None in required_fields.values():
                        logger.warning(f"Skipping earthquake with missing data: {feature['id']}")
                        continue
                    
                    # Convert timestamp to UTC
                    timestamp = timezone.datetime.fromtimestamp(
                        properties['time'] / 1000,
                        timezone.utc
                    )
                    
                    # Only include recent earthquakes
                    if timestamp >= twenty_four_hours_ago:
                        latest_earthquakes.append({
                            'usgs_id': feature['id'],
                            'magnitude': properties['mag'],
                            'place': properties['place'],
                            'time': timestamp,
                            'longitude': geometry['coordinates'][0],
                            'latitude': geometry['coordinates'][1],
                            'depth': geometry['coordinates'][2],
                        })
                
                except (KeyError, ValueError) as e:
                    logger.error(f"Error processing earthquake feature: {e}")
                    continue
            
            # Store earthquakes in a single transaction
            with transaction.atomic():
                stored_count = 0
                for quake_data in latest_earthquakes:
                    earthquake, created = Earthquake.objects.get_or_create(
                        usgs_id=quake_data['usgs_id'],
                        defaults=quake_data
                    )
                    if created:
                        stored_count += 1
                        logger.info(f"Stored new earthquake: {earthquake}")
            
            logger.info(f"Successfully processed {len(latest_earthquakes)} earthquakes. "
                       f"Stored {stored_count} new records.")
            
            return latest_earthquakes
            
        except requests.RequestException as e:
            logger.error(f"Error fetching earthquake data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in earthquake data service: {e}")
            return None

    @classmethod
    def get_alerts(cls):
        """
        Return earthquakes that require alerts (magnitude >= 4.5) from the last 24 hours
        """
        twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
        return Earthquake.objects.filter(
            time__gte=twenty_four_hours_ago,
            magnitude__gte=4.5,
            is_alert_sent=False
        ).order_by('-magnitude')