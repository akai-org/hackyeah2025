from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.apps import apps
from .models import UserReputation


@receiver(post_save, sender=User)
def create_user_reputation(sender, instance, created, **kwargs):
    if created:
        UserReputation.objects.get_or_create(user=instance)


@receiver(post_save, sender='transport.Report')
def update_report_stats(sender, instance, created, **kwargs):
    if created and instance.user:
        reputation, _ = UserReputation.objects.get_or_create(user=instance.user)
        reputation.total_reports_created += 1
        reputation.save()
