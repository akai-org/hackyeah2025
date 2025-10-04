from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from userstats.models import UserReputation, ReportFeedback, ReputationHistory
from transport.models import Report, ReportType, Route, Station
from django.utils import timezone
import random


class Command(BaseCommand):
    help = 'Load mock data for reputation system'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating mock data for reputation system...')

        users = []
        for i in range(1, 11):
            username = f'user{i}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': f'Test{i}',
                    'last_name': f'User{i}'
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(f'✓ Created user: {username}')
            users.append(user)

        for user in users:
            reputation, created = UserReputation.objects.get_or_create(user=user)

            if created or reputation.total_reports_created == 0:
                reports_count = random.randint(0, 30)
                feedbacks_given = random.randint(0, 40)
                positive_received = random.randint(0, min(reports_count * 2, 35))
                negative_received = random.randint(0, min(reports_count, 15))

                reputation.total_reports_created = reports_count
                reputation.total_feedbacks_given = feedbacks_given
                reputation.positive_feedbacks_received = positive_received
                reputation.negative_feedbacks_received = negative_received

                reputation.points = 20 + positive_received - (negative_received * 2)
                reputation.points = max(0, reputation.points)

                reputation.tier = reputation.calculate_tier()
                reputation.last_activity_date = timezone.now()
                reputation.save()

                self.stdout.write(f'  ✓ {user.username}: {reports_count} reports, {positive_received} positive, {negative_received} negative, Tier {reputation.tier}')

        self.stdout.write(self.style.SUCCESS('\n✓ Mock data created successfully!'))
        self.stdout.write(f'Created/updated {len(users)} users with reputation data')

        self.stdout.write('\n=== Sample User Stats ===')
        for user in users[:5]:
            rep = user.reputation
            achievements = rep.get_achievements()
            unlocked = [a for a in achievements if a['unlocked']]
            self.stdout.write(f'{user.username}: Tier {rep.tier}, {len(unlocked)} achievements unlocked')

