"""
URL Configuration for report app
"""
from django.urls import path
from report.views import (
    CreateReportView,
    ReportTypeListView,
    UserReportListView,
    ReportListView,
)

app_name = 'report'

urlpatterns = [
    # Tworzenie raportu użytkownika
    path('reports/create/', CreateReportView.as_view(), name='create-report'),

    # Lista raportów użytkownika
    path('my-reports/', UserReportListView.as_view(), name='my-reports-list'),

    # Lista typów raportów
    path('report-types/', ReportTypeListView.as_view(), name='report-types-list'),

    # Lista wszystkich raportów
    path('reports/', ReportListView.as_view(), name='reports-list'),
]
