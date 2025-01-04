import requests
import logging
from django.utils import timezone
from .models import Earthquake

logger = logging.getLogger(__name__)

class EarthquakeDataService:
    USGS_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    
    @classmethod
    def fetch_recent_earthquakes(cls):
        """
        Fetch recent earthquakes from USGS API and store new ones in the database.
        """
        try:
            response = requests.get(cls.USGS_API_URL, timeout=10)
            response.raise_for_status()  # Raise an error for HTTP errors
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

                # Convert timestamp
                timestamp = timezone.datetime.fromtimestamp(properties['time'] / 1000, timezone.utc)

                # Check if earthquake already exists
                existing_eq = Earthquake.objects.filter(usgs_id=feature['id']).exists()

                if not existing_eq:
                    earthquake = Earthquake.objects.create(
                        usgs_id=feature['id'],
                        magnitude=properties['mag'],
                        place=properties['place'],
                        time=timestamp,
                        longitude=geometry['coordinates'][0],
                        latitude=geometry['coordinates'][1],
                        depth=geometry['coordinates'][2],
                    )
                    
                    # Send alert if magnitude is high
                    if earthquake.magnitude >= 4.5:
                        #cls.send_earthquake_alert(earthquake)
                        logger.info(f"Earthquake detected but email alert not sent: {earthquake}")

            logger.info("Successfully fetched and saved recent earthquake data.")

        except requests.RequestException as e:
            logger.error(f"Error fetching earthquake data: {e}")
    
    @classmethod
    def send_earthquake_alert(cls, earthquake):
        """
        Send email alerts for significant earthquakes.
        """
        from django.core.mail import send_mail
        
        subject = f"Earthquake Alert: {earthquake.place}"
        message = f"""
        Earthquake Detected:
        Location: {earthquake.place}
        Magnitude: {earthquake.magnitude}
        Time: {earthquake.time}
        Coordinates: {earthquake.latitude}, {earthquake.longitude}
        """

        # Replace these emails with actual recipients
        recipients = ['authority1@example.com', 'authority2@example.com']

        try:
            send_mail(
                subject,
                message,
                'earthquake_alerts@yourdomain.com',
                recipients,
                fail_silently=False,
            )
            logger.info(f"Sent earthquake alert for {earthquake.place}")

        except Exception as e:
            logger.error(f"Failed to send earthquake alert: {e}")
