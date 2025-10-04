"""
Modele pojazdów
"""
from django.db import models
from django.core.validators import MinValueValidator

from .carrier import Carrier


class Vehicle(models.Model):
    """Model representing a vehicle (train, bus, tram)"""
    VEHICLE_TYPE = [
        ('TRAIN', 'Train'),
        ('BUS', 'Bus'),
        ('TRAM', 'Tram'),
        ('METRO', 'Metro'),
        ('OTHER', 'Other'),
    ]

    identification_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Vehicle identification number"
    )
    carrier = models.ForeignKey(
        Carrier,
        on_delete=models.CASCADE,
        related_name='vehicles',
        verbose_name="Carrier"
    )
    type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPE,
        default='TRAIN'
    )
    max_speed = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Maximum speed (km/h)",
        help_text="Maximum vehicle speed in km/h"
    )
    average_speed = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        verbose_name="Average speed (km/h)",
        help_text="Average operational speed in km/h (calculated automatically)"
    )
    passenger_capacity = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Passenger capacity"
    )
    active = models.BooleanField(
        default=True,
        help_text="Whether the vehicle is currently in operation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"
        ordering = ['carrier', 'identification_number']

    def __str__(self):
        return f"{self.get_type_display()} {self.identification_number} ({self.carrier.name})"

