"""
Modele użytkowników i biletów
"""
from datetime import timezone

from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .infrastructure import Station
from .route import Route
from .vehicle import Vehicle


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
        from .report import UserStats
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


class JourneyPassenger(models.Model):
    """
    Represents a user currently on a journey.
    A user can only be on one journey at a time.
    This is required to submit reports.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='current_journey',
        verbose_name="User",
        help_text="User can only be on one journey at a time"
    )
    journey = models.ForeignKey(
        'Journey',
        on_delete=models.CASCADE,
        related_name='passengers',
        verbose_name="Journey",
        help_text="The journey user is currently on"
    )

    boarded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Boarding time"
    )
    exited_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Exit time"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether user is still on this journey"
    )

    class Meta:
        verbose_name = "Journey passenger"
        verbose_name_plural = "Journey passengers"
        ordering = ['-boarded_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['journey', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.username} on {self.journey}"

    def clean(self):
        """Validate that user is not already on another journey"""
        if self.pk is None and self.is_active:
            existing = JourneyPassenger.objects.filter(
                user=self.user,
                is_active=True
            ).exists()
            if existing:
                raise ValidationError(
                    f"User {self.user.username} is already on another journey."
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def exit_journey(self):
        """Mark user as exited from journey"""
        from django.utils import timezone
        self.is_active = False
        self.exited_at = timezone.now()
        self.save()

    @classmethod
    def board_user(cls, user, journey, boarding_station, destination_station, ticket=None):
        """Board a user onto a journey"""
        # Exit from any current journey
        cls.objects.filter(user=user, is_active=True).update(
            is_active=False,
            exited_at=timezone.now()
        )

        # Create new boarding
        return cls.objects.create(
            user=user,
            journey=journey,
            boarding_station=boarding_station,
            destination_station=destination_station,
            ticket=ticket,
            is_active=True
        )
