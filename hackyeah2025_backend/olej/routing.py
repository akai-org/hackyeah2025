from django.urls import include, re_path, path
from olej.vehicle_consumer import VehicleConsumer

websocket_urlpatterns = [
    re_path(r"ws/vehicles/(?P<vehicle_id>)", VehicleConsumer.as_asgi()),
]

http_urlpatterns = [
    path("geo/vehicles/", include("olej.views.vehicle_views")),
]
