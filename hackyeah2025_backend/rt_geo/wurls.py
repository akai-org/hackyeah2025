from django.urls import re_path
from rt_geo.vehicle_consumer import VehicleConsumer

websocket_urlpatterns = [
    re_path(r"ws/vehicles/(?P<vehicle_id>)", VehicleConsumer.as_asgi()),
]
