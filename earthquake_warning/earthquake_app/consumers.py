import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.utils import timezone

class EarthquakeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handles WebSocket connection and joins the update group."""
        await self.channel_layer.group_add("earthquake_updates", self.channel_name)
        await self.accept()
        print("✅ WebSocket Connected")

    async def disconnect(self, close_code):
        """Handles WebSocket disconnection and removes from group."""
        await self.channel_layer.group_discard("earthquake_updates", self.channel_name)
        print("❌ WebSocket Disconnected")

    async def send_earthquake_update(self, event):
        """Sends earthquake updates to all connected WebSocket clients."""
        earthquake = event["earthquake"]
        await self.send(text_data=json.dumps(earthquake))
