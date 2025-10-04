"""
Modele infrastruktury: Stacje, Tory, Perony, Połączenia
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from .carrier import StationType


class Station(models.Model):
    """Model representing a station/depot"""
    name = models.CharField(max_length=200, verbose_name="Station name")
    location = models.CharField(
        max_length=500,
        help_text="Address or geographic coordinates"
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude"
    )
    type = models.ForeignKey(
        StationType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stations',
        verbose_name="Station type",
        help_text="Type of station (e.g., major hub, local stop, depot)"
    )
    platform_capacity = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1)],
        verbose_name="Platform capacity",
        help_text="Maximum number of trains that can be at station simultaneously"
    )
    current_occupancy = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Current occupancy",
        help_text="Number of trains currently at the station"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Station"
        verbose_name_plural = "Stations"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_at_capacity(self):
        """Check if station is at full capacity"""
        return self.current_occupancy >= self.platform_capacity

    def can_accommodate_train(self):
        """Check if station can accommodate another train"""
        return self.current_occupancy < self.platform_capacity


class Track(models.Model):
    """
    Model representing a railway track.
    Allows modeling route dependencies - when 2 different platforms
    use the same track in different routes.
    """
    number = models.CharField(max_length=50, unique=True, verbose_name="Track number")
    name = models.CharField(max_length=200, blank=True, verbose_name="Track name/description")
    length_meters = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Track length in meters"
    )
    parent_track = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_tracks',
        help_text="Main track from which this track branches"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Track"
        verbose_name_plural = "Tracks"
        ordering = ['number']

    def __str__(self):
        return f"Track {self.number}" + (f" - {self.name}" if self.name else "")


class Platform(models.Model):
    """Model representing a platform at a station"""
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='platforms',
        verbose_name="Station"
    )
    number = models.CharField(max_length=50, verbose_name="Platform number")
    max_wagons = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        verbose_name="Maximum number of wagons",
        help_text="Maximum number of wagons this platform can accommodate"
    )
    active = models.BooleanField(
        default=True,
        help_text="Whether the platform is currently in use"
    )
    track = models.ForeignKey(
        Track,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='platforms',
        verbose_name="Track",
        help_text="Track assigned to this platform"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Platform"
        verbose_name_plural = "Platforms"
        ordering = ['station', 'number']
        unique_together = [['station', 'number']]

    def __str__(self):
        return f"{self.station.name} - Platform {self.number}"

    def get_track_conflicts(self):
        """
        Returns other platforms using the same track,
        allowing detection of potential conflicts during delays.
        """
        if self.track:
            return Platform.objects.filter(track=self.track).exclude(id=self.id)
        return Platform.objects.none()


class StationConnection(models.Model):
    """Graf połączeń między stacjami - reprezentuje bezpośrednie połączenie kolejowe"""
    from_station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='outgoing_connections',
        verbose_name="From station",
        help_text="Starting station of the connection"
    )
    to_station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='incoming_connections',
        verbose_name="To station",
        help_text="Destination station of the connection"
    )
    distance_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Distance (km)",
        help_text="Physical distance between stations in kilometers"
    )
    estimated_time_minutes = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Estimated travel time (minutes)",
        help_text="Typical travel time between these stations"
    )
    is_bidirectional = models.BooleanField(
        default=True,
        help_text="Whether trains can travel in both directions on this connection"
    )
    max_speed_kmh = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Maximum speed (km/h)",
        help_text="Speed limit on this section"
    )
    active = models.BooleanField(
        default=True,
        help_text="Whether this connection is currently operational"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Station connection"
        verbose_name_plural = "Station connections"
        ordering = ['from_station', 'to_station']
        unique_together = [['from_station', 'to_station']]
        indexes = [
            models.Index(fields=['from_station', 'to_station']),
            models.Index(fields=['active', 'from_station']),
        ]

    def __str__(self):
        direction = "↔" if self.is_bidirectional else "→"
        return f"{self.from_station.name} {direction} {self.to_station.name} ({self.distance_km} km)"

    def get_reverse_connection(self):
        """Get the reverse connection if this is bidirectional"""
        if self.is_bidirectional:
            return StationConnection.objects.filter(
                from_station=self.to_station,
                to_station=self.from_station
            ).first()
        return None

    def create_reverse_connection(self):
        """Create reverse connection if bidirectional and doesn't exist"""
        if self.is_bidirectional:
            reverse_conn, created = StationConnection.objects.get_or_create(
                from_station=self.to_station,
                to_station=self.from_station,
                defaults={
                    'distance_km': self.distance_km,
                    'estimated_time_minutes': self.estimated_time_minutes,
                    'is_bidirectional': True,
                    'max_speed_kmh': self.max_speed_kmh,
                    'active': self.active,
                }
            )
            return reverse_conn
        return None

    def save(self, *args, **kwargs):
        """Override save to automatically create reverse connection if bidirectional"""
        super().save(*args, **kwargs)
        if self.is_bidirectional:
            self.create_reverse_connection()

