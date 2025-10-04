from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserReputation, ReportFeedback, ReputationHistory
from .serializers import (UserReputationSerializer, ReportFeedbackSerializer,
                          ReportFeedbackCreateSerializer, ReputationHistorySerializer)


class UserReputationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserReputation.objects.all()
    serializer_class = UserReputationSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        reputation, created = UserReputation.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(reputation)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def achievements(self, request):
        reputation, created = UserReputation.objects.get_or_create(user=request.user)
        achievements = reputation.get_achievements()

        unlocked = [a for a in achievements if a['unlocked']]
        locked = [a for a in achievements if not a['unlocked']]

        return Response({
            'total_achievements': len(achievements),
            'unlocked_count': len(unlocked),
            'locked_count': len(locked),
            'achievements': achievements,
            'unlocked': unlocked,
            'locked': locked
        })


class ReportFeedbackViewSet(viewsets.ModelViewSet):
    queryset = ReportFeedback.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return ReportFeedbackCreateSerializer
        return ReportFeedbackSerializer

    def get_queryset(self):
        queryset = ReportFeedback.objects.all()
        report_id = self.request.query_params.get('report_id', None)
        if report_id is not None:
            queryset = queryset.filter(report_id=report_id)
        return queryset


class ReputationHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReputationHistory.objects.all()
    serializer_class = ReputationHistorySerializer
    permission_classes = [IsAuthenticated]
