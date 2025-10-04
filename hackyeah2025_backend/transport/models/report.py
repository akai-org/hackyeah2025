"""
Modele raportów i zgłoszeń
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

from .infrastructure import Station
from .route import Route, RoutePoint


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
    User report about an issue during journey.
    Created directly by users who are active passengers.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending verification'),
        ('CONFIRMED', 'Confirmed'),
        ('REJECTED', 'Rejected'),
        ('RESOLVED', 'Resolved'),
    ]

    CATEGORY_CHOICES = [
        ('DELAY', 'Delay (train stopped or moving slowly)'),
        ('TECHNICAL_FAILURE', 'Technical failure (vehicle, signaling, switches)'),
        ('RANDOM_EVENT', 'Random event (accident, passenger illness)'),
        ('INFRASTRUCTURE', 'Infrastructure issues (track maintenance, blocked crossing)'),
        ('OVERCROWDING', 'Overcrowding (no seats, very crowded)'),
        ('WEATHER', 'Weather conditions (snow, storm, heat affecting operations)'),
        ('COMMUNITY_INFO', 'Community information (lost/found items, passenger assistance)'),
        ('OTHER', 'Other'),
    ]

    # User who created the report
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reports',
        verbose_name="Reporting user"
    )

    # Journey passenger proof
    journey_passenger = models.ForeignKey(
        'JourneyPassenger',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name="Journey passenger record",
        help_text="Proves user is currently on the journey"
    )

    journey = models.ForeignKey(
        'Journey',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name="Journey",
        help_text="Specific journey this report is about"
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
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='OTHER',
        verbose_name="Report category",
        help_text="Category of the reported issue"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Status"
    )

    # Report details
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
        upload_to='reports/',
        null=True,
        blank=True,
        verbose_name="Image",
        help_text="Photo evidence of the issue"
    )

    # Staff and verification
    is_staff_report = models.BooleanField(
        default=False,
        verbose_name="Staff report",
        help_text="Whether this report is from verified staff (more credible)"
    )
    confidence_level = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name="Confidence level",
        help_text="How confident the user is about this report (0-1)"
    )

    # Location data
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

    # Timestamps
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
        username = self.user.username
        journey_info = f" [{self.journey}]" if self.journey else ""
        staff_tag = " [STAFF]" if self.is_staff_report else ""
        return f"{username}'s report{staff_tag} - {self.report_type.name}{journey_info}: {self.from_station.name} → {self.to_station.name}"

    def save(self, *args, **kwargs):
        """Override save to auto-detect staff reports"""
        # Auto-detect if user is verified staff
        if self.user and hasattr(self.user, 'profile') and self.user.profile.is_verified:
            self.is_staff_report = True

        super().save(*args, **kwargs)

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
        help_text="Reports that were verified by admins"
    )
    rejected_reports = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Number of rejected reports"
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
        """Recalculate user statistics from reports"""
        reports = Report.objects.filter(user=self.user)

        self.total_reports = reports.count()
        self.confirmed_reports = reports.filter(status='CONFIRMED').count()
        self.rejected_reports = reports.filter(status='REJECTED').count()

        if self.total_reports > 0:
            confirmation_rate = self.confirmed_reports / self.total_reports
            rejection_penalty = self.rejected_reports * 5
            staff_bonus = reports.filter(is_staff_report=True).count() * 10
            self.reputation_score = int((confirmation_rate * 100) + staff_bonus - rejection_penalty)
        else:
            self.reputation_score = 0

        last_report = reports.order_by('-created_at').first()
        if last_report:
            self.last_report_date = last_report.created_at

        self.save()

    @property
    def confirmation_rate(self):
        """Calculate percentage of confirmed reports"""
        if self.total_reports == 0:
            return 0
        return round((self.confirmed_reports / self.total_reports) * 100, 2)
