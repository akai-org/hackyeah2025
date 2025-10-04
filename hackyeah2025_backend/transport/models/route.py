"""
Modele tras i grafów tras
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

from .carrier import Carrier
from .infrastructure import Station, Track, Platform, StationConnection
from .vehicle import Vehicle


class Route(models.Model):
    """Model representing a travel route"""
    name = models.CharField(max_length=200, verbose_name="Route name")
    line_number = models.CharField(
        max_length=50,
        verbose_name="Line number",
        help_text="e.g. IC 1234, Bus 125"
    )
    carrier = models.ForeignKey(
        Carrier,
        on_delete=models.CASCADE,
        related_name='routes',
        verbose_name="Carrier"
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='routes',
        verbose_name="Assigned vehicle"
    )
    active = models.BooleanField(
        default=True,
        help_text="Whether the route is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Route"
        verbose_name_plural = "Routes"
        ordering = ['line_number', 'name']

    def __str__(self):
        return f"{self.line_number} - {self.name}"


class RoutePoint(models.Model):
    """
    Model representing a point on a route (sequence of stops/stations).
    Defines the order of stops and tracks used by the route.
    """
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='route_points',
        verbose_name="Route"
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='route_points',
        verbose_name="Station"
    )
    platform = models.ForeignKey(
        Platform,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='route_points',
        verbose_name="Platform"
    )
    track = models.ForeignKey(
        Track,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='route_points',
        verbose_name="Track",
        help_text="Track used to reach this point"
    )
    sequence = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Order in route",
        help_text="Stop order number in route (1, 2, 3...)"
    )
    scheduled_arrival_time = models.TimeField(
        verbose_name="Scheduled arrival time"
    )
    scheduled_departure_time = models.TimeField(
        verbose_name="Scheduled departure time"
    )
    stop_duration_minutes = models.IntegerField(
        default=2,
        validators=[MinValueValidator(0)],
        verbose_name="Stop duration (minutes)"
    )
    distance_from_previous_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Distance from previous point (km)"
    )

    class Meta:
        verbose_name = "Route point"
        verbose_name_plural = "Route points"
        ordering = ['route', 'sequence']
        unique_together = [['route', 'sequence'], ['route', 'station', 'sequence']]

    def __str__(self):
        return f"{self.route.line_number} - {self.sequence}. {self.station.name}"

    def get_track_conflicts(self):
        """
        Returns other routes using the same track at similar times,
        allowing detection of potential conflicts during delays.
        """
        if self.track:
            return RoutePoint.objects.filter(
                track=self.track
            ).exclude(
                id=self.id
            ).select_related('route', 'station')
        return RoutePoint.objects.none()


class RouteGraph(models.Model):
    """
    Graf trasy - definiuje trasę jako sekwencję połączeń między stacjami.
    Alternatywna reprezentacja Route używająca grafu połączeń.
    """
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='route_graphs',
        verbose_name="Route"
    )
    connection = models.ForeignKey(
        StationConnection,
        on_delete=models.CASCADE,
        related_name='route_graphs',
        verbose_name="Station connection",
        help_text="Connection between two consecutive stations on this route"
    )
    sequence = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Sequence in route",
        help_text="Order of this connection in the route (1, 2, 3...)"
    )
    scheduled_departure_from_first_station = models.TimeField(
        verbose_name="Departure from first station",
        help_text="When the train departs from the first station of this connection"
    )
    scheduled_arrival_at_second_station = models.TimeField(
        verbose_name="Arrival at second station",
        help_text="When the train arrives at the second station of this connection"
    )

    class Meta:
        verbose_name = "Route graph connection"
        verbose_name_plural = "Route graph connections"
        ordering = ['route', 'sequence']
        unique_together = [['route', 'sequence'], ['route', 'connection', 'sequence']]
        indexes = [
            models.Index(fields=['route', 'sequence']),
        ]

    def __str__(self):
        return f"{self.route.line_number} - {self.sequence}. {self.connection}"

    @property
    def from_station(self):
        """Get starting station of this connection"""
        return self.connection.from_station

    @property
    def to_station(self):
        """Get destination station of this connection"""
        return self.connection.to_station

    def get_next_connection(self):
        """Get next connection in the route"""
        return RouteGraph.objects.filter(
            route=self.route,
            sequence=self.sequence + 1
        ).first()

    def get_previous_connection(self):
        """Get previous connection in the route"""
        return RouteGraph.objects.filter(
            route=self.route,
            sequence=self.sequence - 1
        ).first()

    def get_all_stations_on_route(self):
        """Get all stations on this route in order"""
        route_connections = RouteGraph.objects.filter(
            route=self.route
        ).order_by('sequence').select_related('connection__from_station', 'connection__to_station')

        if not route_connections.exists():
            return []

        stations = [route_connections.first().from_station]

        for rg in route_connections:
            stations.append(rg.to_station)

        return stations

