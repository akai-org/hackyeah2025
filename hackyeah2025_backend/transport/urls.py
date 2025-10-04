"""
URL configuration for transport app
"""
from django.urls import path
from transport.views import StationListView, ConnectionSearchView

app_name = 'transport'

urlpatterns = [
    path('stations/', StationListView.as_view(), name='station-list'),
    path('connections/', ConnectionSearchView.as_view(), name='connection-search'),
]
