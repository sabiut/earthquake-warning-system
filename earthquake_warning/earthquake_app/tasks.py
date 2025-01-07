import requests
import logging
from earthquake_warning.earthquake_warning.celery import shared_task
from django.utils import timezone
from django.db import transaction
from .models import Earthquake
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

USGS_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"

@shared_task
def fetch_earthquake_data():
    """
    Celery task to fetch recent earthquake data from the USGS API.
    - Stores new earthquakes in the database.
    - Sends real-time updates via WebSockets.
    - Runs automatically at scheduled intervals.
    """
    try:
        logger.info("⏳ Fetching earthquake data from USGS API...")

        response = requests.get(USGS_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "features" not in data:
            logger.warning("❌ USGS API response is missing 'features' key.")
            return

        twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
        latest_earthquakes = []
        stored_count = 0

        for feature in data.get("features", []):
            try:
                properties = feature.get("properties", {})
                geometry = feature.get("geometry", {})

                # Validate required fields
                if not all([properties.get("mag"), properties.get("place"), properties.get("time"), geometry.get("coordinates")]):
                    logger.warning(f"⚠️ Skipping incomplete earthquake data: {feature.get('id', 'Unknown')}")
                    continue

                timestamp = timezone.datetime.fromtimestamp(properties["time"] / 1000, timezone.utc)

                if timestamp < twenty_four_hours_ago:
                    continue  # Ignore older earthquakes

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
            return

        # Store new earthquakes in the database
        with transaction.atomic():
            channel_layer = get_channel_layer()

            for quake_data in latest_earthquakes:
                earthquake, created = Earthquake.objects.get_or_create(
                    usgs_id=quake_data["usgs_id"], defaults=quake_data
                )

                if created:
                    stored_count += 1
                    logger.info(f"📍 Stored new earthquake: {earthquake}")

                    # Send WebSocket update
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

    except requests.Timeout:
        logger.error("❌ Timeout while fetching earthquake data from USGS API")
    except requests.ConnectionError:
        logger.error("❌ Connection error while accessing USGS API")
    except requests.RequestException as e:
        logger.error(f"❌ Error fetching earthquake data: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error in Celery task: {e}")
