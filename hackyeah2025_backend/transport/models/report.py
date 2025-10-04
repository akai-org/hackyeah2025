"""
Modele raportów i zgłoszeń
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.utils import timezone

from .infrastructure import Station
from .route import Route, RoutePoint
from .user import Ticket
from .weather import Weather


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
