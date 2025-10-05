from django.urls import path
from rt_geo.views import GeoVehicleView

urlpatterns = [
    path("geo/vehicles/", GeoVehicleView.as_view(), name="geo_vehicle_view"),
]
