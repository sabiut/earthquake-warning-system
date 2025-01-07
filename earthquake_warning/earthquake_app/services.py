import requests
import logging
from django.utils import timezone
from django.db import transaction
from .models import Earthquake
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

class EarthquakeDataService:
    USGS_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"

    @classmethod
    def fetch_recent_earthquakes(cls):
        """
        Fetch and store earthquakes from USGS API from the last 24 hours.
        Also pushes real-time updates via WebSockets.
        """
        try:
            logger.info("🔄 Fetching earthquake data from USGS API...")
            response = requests.get(cls.USGS_API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "features" not in data:
                logger.error("❌ Invalid API response: 'features' key missing")
                return None

            twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
            latest_earthquakes = []
            stored_count = 0

            for feature in data.get("features", []):
                try:
                    properties = feature.get("properties", {})
                    geometry = feature.get("geometry", {})

                    required_fields = {
                        "mag": properties.get("mag"),
                        "place": properties.get("place"),
                        "time": properties.get("time"),
                        "coordinates": geometry.get("coordinates"),
                    }

                    if None in required_fields.values():
                        logger.warning(f"⚠️ Skipping earthquake due to missing data: {feature.get('id', 'Unknown')}")
                        continue

                    # Convert timestamp from milliseconds to datetime object
                    timestamp = timezone.datetime.fromtimestamp(properties["time"] / 1000, timezone.utc)

                    if timestamp < twenty_four_hours_ago:
                        continue  # Skip older earthquakes

                    latest_earthquakes.append({
                        "usgs_id": feature["id"],
                        "magnitude": properties["mag"],
                        "place": properties["place"],
                        "time": timestamp,
                        "longitude": geometry["coordinates"][0],
                        "latitude": geometry["coordinates"][1],
                        "depth": geometry["coordinates"][2],
                    })

                except (KeyError, ValueError, IndexError) as e:
                    logger.error(f"⚠️ Error processing earthquake data: {e}")
                    continue

            if not latest_earthquakes:
                logger.info("✅ No new earthquakes found.")
                return None

            # Start database transaction
            with transaction.atomic():
                channel_layer = get_channel_layer()

                for quake_data in latest_earthquakes:
                    earthquake, created = Earthquake.objects.get_or_create(
                        usgs_id=quake_data["usgs_id"], defaults=quake_data
                    )

                    if created:
                        stored_count += 1
                        logger.info(f"📍 Stored new earthquake: {earthquake}")

                        # Send real-time update via WebSockets
                        async_to_sync(channel_layer.group_send)(
                            "earthquake_updates",
                            {
                                "type": "send_earthquake_update",
                                "earthquake": {
                                    "latitude": earthquake.latitude,
                                    "longitude": earthquake.longitude,
                                    "magnitude": earthquake.magnitude,
                                    "depth": earthquake.depth,
                                    "place": earthquake.place,
                                    "time": earthquake.time.isoformat(),
                                    "status": earthquake.status,
                                    "id": earthquake.id,
                                },
                            },
                        )

            logger.info(f"✅ Processed {len(latest_earthquakes)} earthquakes. Stored {stored_count} new records.")
            return latest_earthquakes

        except requests.Timeout:
            logger.error("❌ Timeout while fetching earthquake data from USGS API")
            return None
        except requests.ConnectionError:
            logger.error("❌ Connection error while accessing USGS API")
            return None
        except requests.RequestException as e:
            logger.error(f"❌ Error fetching earthquake data: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error in earthquake data service: {e}")
            return None

    @classmethod
    def get_alerts(cls):
        """
        Retrieve earthquakes that require alerts (magnitude >= 4.5) from the last 24 hours.
        """
        twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
        alerts = Earthquake.objects.filter(
            time__gte=twenty_four_hours_ago,
            magnitude__gte=4.5,
            is_alert_sent=False
        ).order_by('-magnitude')

        logger.info(f"🚨 Found {alerts.count()} earthquakes requiring alerts.")
        return alerts
