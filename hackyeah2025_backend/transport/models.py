from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.utils import timezone


class Carrier(models.Model):
    """Model representing a public transport carrier"""
    name = models.CharField(max_length=200, unique=True, verbose_name="Carrier name")
    priority = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Carrier priority (0-10, where 10 is highest)"
    )
    ticket_purchase_link = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Ticket purchase link"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Carrier"
        verbose_name_plural = "Carriers"
        ordering = ['-priority', 'name']

    def __str__(self):
        return f"{self.name} (priority: {self.priority})"


class StationType(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, verbose_name="Station type name")

    class Meta:
        verbose_name = "Station type"
        verbose_name_plural = "Station types"

    def __str__(self):
        return self.name


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
        from django.utils import timezone
        return timezone.now() < self.valid_until


class UserProfile(models.Model):
    """
    Extended user profile with additional information.
    Extends Django's built-in User model.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="User"
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date of birth"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Phone number"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name="Avatar"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether the user is verified (trusted reporter)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User profile"
        verbose_name_plural = "User profiles"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - Profile"

    def get_stats(self):
        """Get or create user statistics"""
        stats, created = UserStats.objects.get_or_create(user=self.user)
        return stats


class Ticket(models.Model):
    """Ticket purchased by user for a specific route"""
    TICKET_STATUS = [
        ('VALID', 'Valid'),
        ('USED', 'Used'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name="User"
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name="Route"
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name="Assigned vehicle",
        help_text="Specific vehicle user is assigned to"
    )
    from_station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='tickets_from',
        verbose_name="From station"
    )
    to_station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='tickets_to',
        verbose_name="To station"
    )
    purchase_date = models.DateTimeField(auto_now_add=True)
    travel_date = models.DateField(verbose_name="Travel date")
    departure_time = models.TimeField(verbose_name="Scheduled departure time")
    seat_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Seat number"
    )
    ticket_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Ticket number"
    )
    status = models.CharField(
        max_length=20,
        choices=TICKET_STATUS,
        default='VALID'
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Price"
    )

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ['-purchase_date']

    def __str__(self):
        return f"Ticket {self.ticket_number} - {self.user.username} ({self.from_station.name} → {self.to_station.name})"


class ReportType(models.Model):
    """Type of delay/issue report"""
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Report type name"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    severity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Severity level (1-5, where 5 is most severe)"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon name for frontend display"
    )
    color = models.CharField(
        max_length=7,
        default='#FF0000',
        help_text="Color code in HEX format (e.g., #FF0000)"
    )
    active = models.BooleanField(
        default=True,
        help_text="Whether this report type is currently available"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Report type"
        verbose_name_plural = "Report types"
        ordering = ['-severity', 'name']

    def __str__(self):
        return f"{self.name} (severity: {self.severity})"


class Report(models.Model):
    """
    Aggregated report for a specific route section.
    Gets automatically confirmed when 3+ users report the same issue.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending verification'),
        ('CONFIRMED', 'Confirmed'),
        ('REJECTED', 'Rejected'),
        ('RESOLVED', 'Resolved'),
    ]

    journey = models.ForeignKey(
        'Journey',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name="Journey",
        help_text="Specific journey this report is about (optional)"
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name="Route",
        help_text="Route where issue occurred"
    )
    from_station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='reports_from',
        verbose_name="From station",
        help_text="Starting station of the problem section"
    )
    to_station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='reports_to',
        verbose_name="To station",
        help_text="Ending station of the problem section"
    )
    report_type = models.ForeignKey(
        ReportType,
        on_delete=models.PROTECT,
        related_name='reports',
        verbose_name="Report type"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Status"
    )
    average_delay_minutes = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Average delay in minutes",
        help_text="Average delay from all user reports"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Aggregated description",
        help_text="Summary of user reports"
    )
    user_reports_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Number of user reports",
        help_text="How many users reported this issue"
    )
    is_staff_reported = models.BooleanField(
        default=False,
        help_text="Whether any report was made by verified staff"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Confirmed at"
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Resolved at"
    )

    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['route', 'from_station', 'to_station']),
            models.Index(fields=['journey', '-created_at']),
        ]

    def __str__(self):
        journey_info = f" [{self.journey}]" if self.journey else ""
        return f"{self.report_type.name} - {self.route.line_number}{journey_info}: {self.from_station.name} → {self.to_station.name} ({self.user_reports_count} reports, {self.get_status_display()})"

    def update_status(self):
        """Check if report should be auto-confirmed based on user reports count"""
        is_confirmed = self.user_reports_count > 3 or self.is_staff_reported

        if is_confirmed and self.status == 'PENDING':
            self.status = 'CONFIRMED'
            self.confirmed_at = timezone.now()
            self.save(update_fields=['status', 'confirmed_at'])
            return True
        return False

    def recalculate_metrics(self):
        """Recalculate average delay and description from user reports"""
        #get random value based on report besed on connection
        user_reports = self.user_reports.all()
        total_delay = sum([ur.delay_minutes or 0 for ur in user_reports])
        count = user_reports.count()
        self.user_reports_count = count
        self.average_delay_minutes = total_delay // count if count > 0 else None
        self.is_staff_reported = user_reports.filter(is_staff_report=True).exists()
        self.description = "; ".join([ur.description for ur in user_reports if ur.description])
        self.save(update_fields=['user_reports_count', 'average_delay_minutes', 'is_staff_reported', 'description', 'updated_at'])


    def get_affected_route_section(self):
        """Get all route points between from_station and to_station"""
        route_points = RoutePoint.objects.filter(
            route=self.route
        ).order_by('sequence')

        from_point = route_points.filter(station=self.from_station).first()
        to_point = route_points.filter(station=self.to_station).first()

        if from_point and to_point:
            return route_points.filter(
                sequence__gte=from_point.sequence,
                sequence__lte=to_point.sequence
            )
        return RoutePoint.objects.none()


class UserReport(models.Model):
    """
    Individual user's report about an issue.
    Multiple user reports get aggregated into a single Report.
    """
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='user_reports',
        verbose_name="Aggregated report"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='user_reports',
        verbose_name="Reporting user"
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name="Associated ticket",
        help_text="Ticket that proves user was on this route"
    )
    is_staff_report = models.BooleanField(
        default=False,
        verbose_name="Staff report",
        help_text="Whether this report is from railway staff (more credible)"
    )
    confidence_level = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name="Confidence level",
        help_text="How confident the user is about this report (0-1, where 1 is very confident)"
    )
    delay_minutes = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Delay in minutes",
        help_text="User's reported delay duration"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="User's description of the issue"
    )
    image = models.ImageField(
        upload_to='user_reports/',
        null=True,
        blank=True,
        verbose_name="Image"
    )
    location_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="User location latitude"
    )
    location_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="User location longitude"
    )
    weather_condition = models.ForeignKey(
        Weather,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name="Weather at time of report"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User report"
        verbose_name_plural = "User reports"
        ordering = ['-created_at']
        unique_together = [['report', 'user']]

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        staff_tag = " [STAFF]" if self.is_staff_report else ""
        return f"{username}'s report{staff_tag} on {self.report}"

    def save(self, *args, **kwargs):
        """Override save to update parent Report metrics"""
        is_new = self.pk is None

        # Auto-detect if user is staff
        if self.user and self.user.is_staff:
            self.is_staff_report = True

        super().save(*args, **kwargs)

        if is_new:
            self.report.recalculate_metrics()


class UserStats(models.Model):
    """Statistics for user's reporting activity"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='stats',
        verbose_name="User"
    )
    total_reports = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Total number of reports"
    )
    confirmed_reports = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Number of confirmed reports",
        help_text="Reports that were verified by community or admins"
    )
    rejected_reports = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Number of rejected reports"
    )
    total_confirmations_given = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Total confirmations given",
        help_text="How many times user confirmed other users' reports"
    )
    reputation_score = models.IntegerField(
        default=0,
        help_text="User reputation based on report accuracy"
    )
    last_report_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last report date"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User statistics"
        verbose_name_plural = "User statistics"

    def __str__(self):
        return f"{self.user.username} - Stats (Reports: {self.total_reports}, Confirmed: {self.confirmed_reports})"

    def update_stats(self):
        """Recalculate user statistics from user reports"""
        user_reports = UserReport.objects.filter(user=self.user)

        self.total_reports = user_reports.count()
        confirmed_user_reports = user_reports.filter(report__status='CONFIRMED')
        self.confirmed_reports = confirmed_user_reports.count()

        rejected_user_reports = user_reports.filter(report__status='REJECTED')
        self.rejected_reports = rejected_user_reports.count()

        if self.total_reports > 0:
            confirmation_rate = self.confirmed_reports / self.total_reports
            rejection_penalty = self.rejected_reports * 5
            staff_bonus = user_reports.filter(is_staff_report=True).count() * 10
            self.reputation_score = int((confirmation_rate * 100) + staff_bonus - rejection_penalty)
        else:
            self.reputation_score = 0

        last_report = user_reports.order_by('-created_at').first()
        if last_report:
            self.last_report_date = last_report.created_at

        self.save()

    @property
    def confirmation_rate(self):
        """Calculate percentage of confirmed reports"""
        if self.total_reports == 0:
            return 0
        return round((self.confirmed_reports / self.total_reports) * 100, 2)


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


class StationConnection(models.Model):
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


class RouteGraph(models.Model):
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

