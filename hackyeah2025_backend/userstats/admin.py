from django.contrib import admin
from .models import UserReputation, ReportFeedback, ReputationHistory


@admin.register(UserReputation)
class UserReputationAdmin(admin.ModelAdmin):
    list_display = ['user', 'tier', 'points', 'total_reports_created', 'positive_feedbacks_received', 'negative_feedbacks_received', 'updated_at']
    list_filter = ['tier', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-points']


@admin.register(ReportFeedback)
class ReportFeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'report', 'feedback_type', 'created_at']
    list_filter = ['feedback_type', 'created_at']
    search_fields = ['user__username', 'report__id']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(ReputationHistory)
class ReputationHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'points_change', 'points_after', 'reason', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'reason']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
