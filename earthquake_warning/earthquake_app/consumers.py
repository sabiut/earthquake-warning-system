import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Earthquake
from django.utils import timezone

class EarthquakeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("✅ WebSocket Connected")

    async def disconnect(self, close_code):
        print("❌ WebSocket Disconnected")

    async def receive(self, text_data):
        """
        Send real-time earthquake updates.
        """
        earthquakes = Earthquake.objects.filter(time__gte=timezone.now() - timezone.timedelta(days=1))
        earthquake_data = [{
            "latitude": eq.latitude,
            "longitude": eq.longitude,
            "magnitude": eq.magnitude,
            "depth": eq.depth,
            "place": eq.place,
            "time": eq.time.isoformat(),
            "status": eq.status,
        } for eq in earthquakes]

        await self.send(text_data=json.dumps({
            "earthquakes": earthquake_data,
        }))
