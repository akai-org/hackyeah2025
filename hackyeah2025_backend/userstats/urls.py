from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserReputationViewSet, ReportFeedbackViewSet, ReputationHistoryViewSet

router = DefaultRouter()
router.register(r'reputation', UserReputationViewSet, basename='reputation')
router.register(r'feedback', ReportFeedbackViewSet, basename='feedback')
router.register(r'history', ReputationHistoryViewSet, basename='history')

urlpatterns = [
    path('', include(router.urls)),
]

