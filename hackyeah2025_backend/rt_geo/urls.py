from django.urls import re_path, path
from rt_geo.vehicle_consumer import VehicleConsumer
from rt_geo.views import GeoVehicleView

websocket_urlpatterns = [
    re_path(r"ws/vehicles/(?P<vehicle_id>)", VehicleConsumer.as_asgi()),
]

urlpatterns = [
    path("geo/vehicles/", GeoVehicleView.as_view(), name="geo_vehicle_view"),
]
