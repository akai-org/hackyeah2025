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

    def get_achievements(self):
        achievements = []

        ACHIEVEMENTS_CONFIG = [
            {
                'id': 'first_steps',
                'name': 'First Steps',
                'description': 'Create your first report',
                'icon': '🚀',
                'threshold': 1,
                'current': self.total_reports_created,
                'type': 'reports'
            },
            {
                'id': 'reporter',
                'name': 'Active Reporter',
                'description': 'Create 5 reports',
                'icon': '📝',
                'threshold': 5,
                'current': self.total_reports_created,
                'type': 'reports'
            },
            {
                'id': 'veteran_reporter',
                'name': 'Veteran Reporter',
                'description': 'Create 10 reports',
                'icon': '🏆',
                'threshold': 10,
                'current': self.total_reports_created,
                'type': 'reports'
            },
            {
                'id': 'master_reporter',
                'name': 'Master Reporter',
                'description': 'Create 25 reports',
                'icon': '👑',
                'threshold': 25,
                'current': self.total_reports_created,
                'type': 'reports'
            },
            {
                'id': 'legend_reporter',
                'name': 'Legend Reporter',
                'description': 'Create 50 reports',
                'icon': '💎',
                'threshold': 50,
                'current': self.total_reports_created,
                'type': 'reports'
            },
            {
                'id': 'helpful',
                'name': 'Helpful',
                'description': 'Receive 5 positive feedbacks',
                'icon': '👍',
                'threshold': 5,
                'current': self.positive_feedbacks_received,
                'type': 'positive_feedback'
            },
            {
                'id': 'trusted',
                'name': 'Trusted Source',
                'description': 'Receive 10 positive feedbacks',
                'icon': '⭐',
                'threshold': 10,
                'current': self.positive_feedbacks_received,
                'type': 'positive_feedback'
            },
            {
                'id': 'community_hero',
                'name': 'Community Hero',
                'description': 'Receive 25 positive feedbacks',
                'icon': '🌟',
                'threshold': 25,
                'current': self.positive_feedbacks_received,
                'type': 'positive_feedback'
            },
            {
                'id': 'golden_standard',
                'name': 'Golden Standard',
                'description': 'Receive 50 positive feedbacks',
                'icon': '🏅',
                'threshold': 50,
                'current': self.positive_feedbacks_received,
                'type': 'positive_feedback'
            },
            {
                'id': 'feedback_giver',
                'name': 'Feedback Giver',
                'description': 'Give feedback 10 times',
                'icon': '💬',
                'threshold': 10,
                'current': self.total_feedbacks_given,
                'type': 'feedback_given'
            },
            {
                'id': 'community_supporter',
                'name': 'Community Supporter',
                'description': 'Give feedback 25 times',
                'icon': '🤝',
                'threshold': 25,
                'current': self.total_feedbacks_given,
                'type': 'feedback_given'
            },
            {
                'id': 'judge',
                'name': 'The Judge',
                'description': 'Give feedback 50 times',
                'icon': '⚖️',
                'threshold': 50,
                'current': self.total_feedbacks_given,
                'type': 'feedback_given'
            },
            {
                'id': 'critic',
                'name': 'Professional Critic',
                'description': 'Give feedback 100 times',
                'icon': '🎯',
                'threshold': 100,
                'current': self.total_feedbacks_given,
                'type': 'feedback_given'
            },
            {
                'id': 'tier_2',
                'name': 'Trusted User',
                'description': 'Reach Tier 2',
                'icon': '🥉',
                'threshold': 2,
                'current': self.tier,
                'type': 'tier'
            },
            {
                'id': 'tier_3',
                'name': 'Experienced User',
                'description': 'Reach Tier 3',
                'icon': '🥈',
                'threshold': 3,
                'current': self.tier,
                'type': 'tier'
            },
            {
                'id': 'tier_4',
                'name': 'Expert User',
                'description': 'Reach Tier 4',
                'icon': '🥇',
                'threshold': 4,
                'current': self.tier,
                'type': 'tier'
            },
            {
                'id': 'early_bird',
                'name': 'Early Bird',
                'description': 'Be one of the first 100 users',
                'icon': '🐦',
                'threshold': 1,
                'current': 1 if self.user.id <= 100 else 0,
                'type': 'special'
            },
            {
                'id': 'night_owl',
                'name': 'Night Owl',
                'description': 'Create 5 reports (simulated night activity)',
                'icon': '🦉',
                'threshold': 5,
                'current': self.total_reports_created,
                'type': 'special'
            },
            {
                'id': 'speed_demon',
                'name': 'Speed Demon',
                'description': 'Give 20 feedbacks quickly',
                'icon': '⚡',
                'threshold': 20,
                'current': self.total_feedbacks_given,
                'type': 'special'
            },
            {
                'id': 'social_butterfly',
                'name': 'Social Butterfly',
                'description': 'Interact with community 30 times',
                'icon': '🦋',
                'threshold': 30,
                'current': self.total_feedbacks_given + self.total_reports_created,
                'type': 'special'
            },
            {
                'id': 'survivor',
                'name': 'Survivor',
                'description': 'Recover from 5 negative feedbacks',
                'icon': '💪',
                'threshold': 5,
                'current': self.negative_feedbacks_received,
                'type': 'special'
            },
            {
                'id': 'phoenix',
                'name': 'Phoenix',
                'description': 'Rise again after 10 negative feedbacks',
                'icon': '🔥',
                'threshold': 10,
                'current': self.negative_feedbacks_received,
                'type': 'special'
            },
            {
                'id': 'balanced',
                'name': 'Perfectly Balanced',
                'description': 'Have equal positive and negative feedbacks (min 10 each)',
                'icon': '☯️',
                'threshold': 1,
                'current': 1 if (self.positive_feedbacks_received >= 10 and
                                 self.negative_feedbacks_received >= 10 and
                                 abs(self.positive_feedbacks_received - self.negative_feedbacks_received) <= 2) else 0,
                'type': 'special'
            },
            {
                'id': 'optimist',
                'name': 'Eternal Optimist',
                'description': 'Have 90% positive feedback rate (min 20 feedbacks)',
                'icon': '😊',
                'threshold': 1,
                'current': 1 if (self.positive_feedbacks_received + self.negative_feedbacks_received >= 20 and
                                 self.positive_feedbacks_received / max(1, self.positive_feedbacks_received + self.negative_feedbacks_received) >= 0.9) else 0,
                'type': 'special'
            },
            {
                'id': 'train_spotter',
                'name': 'Train Spotter',
                'description': 'Create reports regularly',
                'icon': '🚂',
                'threshold': 15,
                'current': self.total_reports_created,
                'type': 'fun'
            },
            {
                'id': 'detective',
                'name': 'Transport Detective',
                'description': 'Report various issues accurately',
                'icon': '🔍',
                'threshold': 20,
                'current': self.total_reports_created,
                'type': 'fun'
            },
            {
                'id': 'helpful_hand',
                'name': 'Helpful Hand',
                'description': 'Help others by giving feedback',
                'icon': '✋',
                'threshold': 15,
                'current': self.total_feedbacks_given,
                'type': 'fun'
            },
            {
                'id': 'reliable',
                'name': 'Mr. Reliable',
                'description': 'Maintain high accuracy in reports',
                'icon': '🎖️',
                'threshold': 1,
                'current': 1 if (self.total_reports_created >= 10 and
                                 self.positive_feedbacks_received > self.negative_feedbacks_received * 2) else 0,
                'type': 'fun'
            },
            {
                'id': 'century_club',
                'name': 'Century Club',
                'description': 'Reach 100 total activities',
                'icon': '💯',
                'threshold': 100,
                'current': self.total_reports_created + self.total_feedbacks_given,
                'type': 'milestone'
            },
            {
                'id': 'veteran',
                'name': 'Veteran Member',
                'description': 'Be active for a long time',
                'icon': '🎂',
                'threshold': 1,
                'current': 1 if self.total_reports_created + self.total_feedbacks_given >= 50 else 0,
                'type': 'milestone'
            },
        ]

        for achievement in ACHIEVEMENTS_CONFIG:
            is_unlocked = achievement['current'] >= achievement['threshold']
            progress = min(100, int((achievement['current'] / achievement['threshold']) * 100))

            achievements.append({
                'id': achievement['id'],
                'name': achievement['name'],
                'description': achievement['description'],
                'icon': achievement['icon'],
                'unlocked': is_unlocked,
                'progress': progress,
                'current': achievement['current'],
                'threshold': achievement['threshold'],
                'type': achievement['type']
            })

        return achievements


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
