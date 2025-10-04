"""
Modele podróży i statusów
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

from .infrastructure import Station, Platform
from .route import Route, RoutePoint
from .vehicle import Vehicle


class Journey(models.Model):
    """
    Represents a specific journey/trip of a vehicle on a route.
    This is an instance of a Route at a specific date and time.
    """
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('BOARDING', 'Boarding'),
        ('DEPARTED', 'Departed'),
        ('IN_TRANSIT', 'In transit'),
        ('DELAYED', 'Delayed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]

    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='journeys',
        verbose_name="Route"
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        related_name='journeys',
        verbose_name="Assigned vehicle",
        help_text="Specific vehicle making this journey"
    )
    journey_date = models.DateField(
        verbose_name="Journey date",
        help_text="Date when this journey takes place"
    )
    scheduled_departure = models.DateTimeField(
        verbose_name="Scheduled departure time",
        help_text="When the journey is scheduled to start"
    )
    actual_departure = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Actual departure time"
    )
    scheduled_arrival = models.DateTimeField(
        verbose_name="Scheduled arrival time",
        help_text="When the journey is scheduled to end at final station"
    )
    actual_arrival = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Actual arrival time"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SCHEDULED',
        verbose_name="Journey status"
    )
    current_delay_minutes = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Current delay (minutes)",
        help_text="Current delay in minutes"
    )
    current_station = models.ForeignKey(
        Station,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_journeys',
        verbose_name="Current station",
        help_text="Station where vehicle currently is"
    )
    next_station = models.ForeignKey(
        Station,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_journeys',
        verbose_name="Next station"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Journey"
        verbose_name_plural = "Journeys"
        ordering = ['-journey_date', '-scheduled_departure']
        indexes = [
            models.Index(fields=['journey_date', 'route']),
            models.Index(fields=['status', '-journey_date']),
            models.Index(fields=['vehicle', '-journey_date']),
        ]

    def __str__(self):
        return f"{self.route.line_number} - {self.journey_date} ({self.get_status_display()})"

    @property
    def start_station(self):
        """Get first station of the journey"""
        first_point = self.route.route_points.order_by('sequence').first()
        return first_point.station if first_point else None

    @property
    def end_station(self):
        """Get last station of the journey"""
        last_point = self.route.route_points.order_by('-sequence').first()
        return last_point.station if last_point else None

    def get_all_stations(self):
        """Get all stations on this journey in order"""
        return [rp.station for rp in self.route.route_points.order_by('sequence')]

    def calculate_delay(self):
        """Calculate current delay based on schedule"""
        now = timezone.now()

        if self.actual_departure and self.scheduled_departure:
            delay = (self.actual_departure - self.scheduled_departure).total_seconds() / 60
            self.current_delay_minutes = max(0, int(delay))
            self.save(update_fields=['current_delay_minutes'])

        return self.current_delay_minutes

    def save(self, *args, **kwargs):
        """Override save to create JourneyStatus for each RoutePoint automatically"""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Automatycznie twórz JourneyStatus dla każdego RoutePoint
            for route_point in self.route.route_points.all():
                scheduled_arrival = timezone.datetime.combine(
                    self.journey_date,
                    route_point.scheduled_arrival_time
                )
                scheduled_departure = timezone.datetime.combine(
                    self.journey_date,
                    route_point.scheduled_departure_time
                )

                JourneyStatus.objects.get_or_create(
                    journey=self,
                    route_point=route_point,
                    defaults={
                        'scheduled_arrival': scheduled_arrival,
                        'scheduled_departure': scheduled_departure,
                        'delay_minutes': 0,
                    }
                )


class JourneyStatus(models.Model):
    """
    Tracks the status of a journey at each station.
    Records actual arrival/departure times vs scheduled times.
    """
    journey = models.ForeignKey(
        Journey,
        on_delete=models.CASCADE,
        related_name='station_statuses',
        verbose_name="Journey"
    )
    route_point = models.ForeignKey(
        RoutePoint,
        on_delete=models.CASCADE,
        related_name='journey_statuses',
        verbose_name="Route point"
    )
    scheduled_arrival = models.DateTimeField(
        verbose_name="Scheduled arrival"
    )
    actual_arrival = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Actual arrival"
    )
    scheduled_departure = models.DateTimeField(
        verbose_name="Scheduled departure"
    )
    actual_departure = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Actual departure"
    )
    delay_minutes = models.IntegerField(
        default=0,
        verbose_name="Delay at this station (minutes)"
    )
    platform_changed = models.BooleanField(
        default=False,
        help_text="Whether platform was changed from original"
    )
    actual_platform = models.ForeignKey(
        Platform,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journey_statuses',
        verbose_name="Actual platform used"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Journey station status"
        verbose_name_plural = "Journey station statuses"
        ordering = ['journey', 'route_point__sequence']
        unique_together = [['journey', 'route_point']]

    def __str__(self):
        return f"{self.journey} at {self.route_point.station.name}"

    def calculate_delay(self):
        """Calculate delay at this station"""
        if self.actual_arrival and self.scheduled_arrival:
            delay = (self.actual_arrival - self.scheduled_arrival).total_seconds() / 60
            self.delay_minutes = int(delay)
            self.save(update_fields=['delay_minutes'])
        return self.delay_minutes

