"""
Modele pogody
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from .infrastructure import Station


class Weather(models.Model):
    """Weather conditions affecting route performance"""
    WEATHER_CONDITIONS = [
        ('CLEAR', 'Clear'),
        ('RAIN', 'Rain'),
        ('SNOW', 'Snow'),
        ('FOG', 'Fog'),
        ('STORM', 'Storm'),
        ('ICE', 'Ice'),
        ('WIND', 'Strong wind'),
        ("EXTREME", "Extreme conditions")
    ]

    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='weather_conditions',
        verbose_name="Station"
    )
    condition = models.CharField(
        max_length=20,
        choices=WEATHER_CONDITIONS,
        verbose_name="Weather condition"
    )
    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="Temperature (°C)"
    )
    speed_impact_percent = models.IntegerField(
        default=0,
        validators=[MinValueValidator(-50), MaxValueValidator(0)],
        verbose_name="Speed impact (%)",
        help_text="Negative percentage impact on vehicle speed (e.g., -20 means 20% slower)"
    )
    visibility_meters = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Visibility (meters)"
    )
    recorded_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(
        verbose_name="Valid until",
        help_text="When this weather data expires"
    )

    class Meta:
        verbose_name = "Weather condition"
        verbose_name_plural = "Weather conditions"
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.station.name} - {self.get_condition_display()} ({self.recorded_at})"

    @property
    def is_valid(self):
        return timezone.now() < self.valid_until

