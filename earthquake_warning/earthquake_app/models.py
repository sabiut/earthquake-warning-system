from django.db import models
from django.utils import timezone

class Earthquake(models.Model):
    STATUS_CHOICES = [
        ('alert', 'Alert'),
        ('warning', 'Warning'),
        ('safe', 'Safe'),
    ]

    usgs_id = models.CharField(max_length=100, unique=True)
    magnitude = models.FloatField()
    place = models.CharField(max_length=255)
    time = models.DateTimeField()
    
    # Geographical coordinates
    longitude = models.FloatField()
    latitude = models.FloatField()
    depth = models.FloatField()
    
    is_alert_sent = models.BooleanField(default=False)
    
    # New status field
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='safe')

    @classmethod
    def get_recent_earthquakes(cls, years=2):
        two_years_ago = timezone.now() - timezone.timedelta(days=years*365)
        return cls.objects.filter(time__gte=two_years_ago).order_by('-magnitude')

    def save(self, *args, **kwargs):
        """Automatically assign status based on magnitude."""
        if self.magnitude >= 5.0:
            self.status = 'alert'
        elif self.magnitude >= 3.0:
            self.status = 'warning'
        else:
            self.status = 'safe'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.place} - Mag {self.magnitude} on {self.time}"
