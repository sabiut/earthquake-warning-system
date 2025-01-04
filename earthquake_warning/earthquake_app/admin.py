from django.contrib import admin
from .models import Earthquake

@admin.register(Earthquake)
class EarthquakeAdmin(admin.ModelAdmin):
    list_display = ('place', 'magnitude', 'time', 'latitude', 'longitude', 'depth', 'is_alert_sent')
    search_fields = ('place', 'magnitude')
    list_filter = ('magnitude', 'time', 'is_alert_sent')
    ordering = ('-time',)
