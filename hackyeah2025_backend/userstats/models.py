from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone


class UserReputation(models.Model):
    TIER_CHOICES = [
        (1, 'Beginner'),
        (2, 'Trusted'),
        (3, 'Experienced'),
        (4, 'Expert'),
    ]

    TIER_THRESHOLDS = {
        1: 0,
        2: 20,
        3: 40,
        4: 60,
    }

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='reputation',
        verbose_name="User"
    )

    points = models.IntegerField(
        default=20,
        verbose_name="Reputation points"
    )

    tier = models.IntegerField(
        default=1,
        choices=TIER_CHOICES,
        verbose_name="Reputation tier"
    )

    total_reports_created = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Total reports created"
    )

    total_feedbacks_given = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Total feedbacks given"
    )

    positive_feedbacks_received = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Positive feedbacks received"
    )

    negative_feedbacks_received = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Negative feedbacks received"
    )

    negative_points_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Negative points count"
    )

    last_activity_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last activity date"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User reputation"
        verbose_name_plural = "User reputations"
        ordering = ['-points']

    def __str__(self):
        return f"{self.user.username} - Tier {self.tier} ({self.points} pts)"

    def calculate_tier(self):
        if self.points >= self.TIER_THRESHOLDS[4]:
            return 4
        elif self.points >= self.TIER_THRESHOLDS[3]:
            return 3
        elif self.points >= self.TIER_THRESHOLDS[2]:
            return 2
        else:
            return 1

    def update_tier(self):
        old_tier = self.tier
        self.tier = self.calculate_tier()
        if old_tier != self.tier:
            self.save(update_fields=['tier', 'updated_at'])
            return True
        return False

    def add_points(self, amount, reason=""):
        self.points += amount
        if amount < 0:
            self.negative_points_count += abs(amount)
        self.update_tier()
        self.save()

        ReputationHistory.objects.create(
            user=self.user,
            points_change=amount,
            points_after=self.points,
            reason=reason
        )

    def remove_negative_point(self, reason="Active in app"):
        if self.negative_points_count > 0:
            self.negative_points_count -= 1
            self.points += 1
            self.update_tier()
            self.save()

            ReputationHistory.objects.create(
                user=self.user,
                points_change=1,
                points_after=self.points,
                reason=reason
            )
            return True
        return False


class ReportFeedback(models.Model):
    FEEDBACK_CHOICES = [
        ('POSITIVE', 'Confirm'),
        ('NEGATIVE', 'Reject'),
    ]

    report = models.ForeignKey(
        'transport.Report',
        on_delete=models.CASCADE,
        related_name='feedbacks',
        verbose_name="Report"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='given_feedbacks',
        verbose_name="User"
    )

    feedback_type = models.CharField(
        max_length=10,
        choices=FEEDBACK_CHOICES,
        verbose_name="Feedback type"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Report feedback"
        verbose_name_plural = "Report feedbacks"
        unique_together = ['report', 'user']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report', 'feedback_type']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.feedback_type} on report #{self.report.id}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            giver_reputation, _ = UserReputation.objects.get_or_create(user=self.user)
            giver_reputation.total_feedbacks_given += 1
            giver_reputation.last_activity_date = timezone.now()
            giver_reputation.save()

            if self.report.user:
                author_reputation, _ = UserReputation.objects.get_or_create(user=self.report.user)

                if self.feedback_type == 'POSITIVE':
                    author_reputation.positive_feedbacks_received += 1
                    author_reputation.add_points(1, f"Positive feedback for report #{self.report.id}")
                else:
                    author_reputation.negative_feedbacks_received += 1
                    author_reputation.add_points(-2, f"Negative feedback for report #{self.report.id}")

            self.check_report_validity()

    def check_report_validity(self):
        feedbacks = ReportFeedback.objects.filter(report=self.report)
        total_feedbacks = feedbacks.count()
        negative_feedbacks = feedbacks.filter(feedback_type='NEGATIVE').count()

        if negative_feedbacks >= 3 and total_feedbacks > 0:
            negative_percentage = (negative_feedbacks / total_feedbacks) * 100
            if negative_percentage >= 30:
                self.report.status = 'REJECTED'
                self.report.save()

                ReputationHistory.objects.create(
                    user=self.report.user,
                    points_change=0,
                    points_after=self.report.user.reputation.points if hasattr(self.report.user, 'reputation') else 0,
                    reason=f"Report #{self.report.id} rejected by community ({negative_percentage:.1f}% negative)"
                )


class ReputationHistory(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reputation_history',
        verbose_name="User"
    )

    points_change = models.IntegerField(
        verbose_name="Points change"
    )

    points_after = models.IntegerField(
        verbose_name="Points after"
    )

    reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Reason"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reputation history"
        verbose_name_plural = "Reputation histories"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        sign = "+" if self.points_change >= 0 else ""
        return f"{self.user.username} {sign}{self.points_change} pts ({self.reason})"
