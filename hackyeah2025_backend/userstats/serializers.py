from rest_framework import serializers
from .models import UserReputation, ReportFeedback, ReputationHistory


class UserReputationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    tier_display = serializers.CharField(source='get_tier_display', read_only=True)

    class Meta:
        model = UserReputation
        fields = ['id', 'user', 'username', 'tier', 'tier_display', 'total_reports_created',
                  'total_feedbacks_given', 'positive_feedbacks_received',
                  'negative_feedbacks_received', 'last_activity_date', 'created_at']
        read_only_fields = ['user', 'tier', 'total_reports_created', 'total_feedbacks_given',
                           'positive_feedbacks_received', 'negative_feedbacks_received',
                           'last_activity_date', 'created_at']


class ReportFeedbackSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ReportFeedback
        fields = ['id', 'report', 'user', 'username', 'feedback_type', 'created_at']
        read_only_fields = ['user', 'created_at']


class ReportFeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportFeedback
        fields = ['report', 'feedback_type']

    def validate(self, data):
        user = self.context['request'].user
        report = data['report']

        if ReportFeedback.objects.filter(user=user, report=report).exists():
            raise serializers.ValidationError("You have already given feedback for this report")

        if report.user == user:
            raise serializers.ValidationError("You cannot give feedback on your own report")

        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ReputationHistorySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ReputationHistory
        fields = ['id', 'user', 'username', 'points_change', 'points_after', 'reason', 'created_at']
        read_only_fields = ['user', 'points_change', 'points_after', 'reason', 'created_at']
