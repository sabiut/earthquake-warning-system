import requests
import logging
from celery import shared_task
from django.utils import timezone
from .models import Earthquake

logger = logging.getLogger(__name__)

USGS_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"

@shared_task
def fetch_earthquake_data():
    """
    Fetch recent earthquakes from the USGS API and store new ones in the database.
    This function runs as a scheduled Celery task.
    """
    try:
        response = requests.get(USGS_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'features' not in data:
            logger.warning("USGS API response is missing 'features' key.")
            return

        for feature in data['features']:
            properties = feature['properties']
            geometry = feature['geometry']

            if not properties.get('mag') or not properties.get('place') or not properties.get('time'):
                logger.warning(f"Skipping incomplete earthquake data: {feature}")
                continue

            timestamp = timezone.datetime.fromtimestamp(properties['time'] / 1000, timezone.utc)

            if not Earthquake.objects.filter(usgs_id=feature['id']).exists():
                Earthquake.objects.create(
                    usgs_id=feature['id'],
                    magnitude=properties['mag'],
                    place=properties['place'],
                    time=timestamp,
                    longitude=geometry['coordinates'][0],
                    latitude=geometry['coordinates'][1],
                    depth=geometry['coordinates'][2],
                )

        logger.info("Successfully fetched and saved earthquake data.")

    except requests.RequestException as e:
        logger.error(f"Error fetching earthquake data: {e}")
