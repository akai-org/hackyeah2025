from django.views import View
from django.http import HttpResponse, HttpRequest
from rt_geo.models import UserData
from rt_geo.geo_tracker import GeoTracker


class GeoVehicleView(View):
    tracker = GeoTracker()

    def get(self, request: HttpRequest, *args, **kwargs):
        request_data = request.GET
        try:
            user_data = UserData.model_validate(request_data)
            self.tracker.get_latest_location(
                location=user_data.location,
                zoom=user_data.zoom,
                map_width=user_data.width,
                map_height=user_data.height,
            )
            return HttpResponse("Hello, this is the GeoVehicleView GET response.")
        except Exception as e:
            return HttpResponse(f"Invalid request data: {e}", status=400)
