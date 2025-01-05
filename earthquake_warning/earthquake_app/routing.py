from django.urls import path
from .consumers import EarthquakeConsumer

websocket_urlpatterns = [
    path("ws/earthquakes/", EarthquakeConsumer.as_asgi()),
]
