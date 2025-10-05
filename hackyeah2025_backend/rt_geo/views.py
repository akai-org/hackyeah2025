from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rt_geo.models import UserData
from rt_geo.geo_tracker import GeoTracker


class GeoVehicleView(APIView):
    """
    Endpoint for retrieving realtime geolocation data of vehicles.
    """

    tracker = GeoTracker()

    @extend_schema(
        summary="Get vehicle geolocation data",
        description="Retrieve the latest geolocation data for vehicles based on user parameters",
        parameters=[
            OpenApiParameter(
                name="location",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Center location for the map in 'lat,lng' format",
            ),
            OpenApiParameter(
                name="zoom",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Zoom level for the map (1-20)",
            ),
            OpenApiParameter(
                name="width",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Width of the map in pixels",
            ),
            OpenApiParameter(
                name="height",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Height of the map in pixels",
            ),
        ],
        responses={
            200: OpenApiTypes.STR,
            400: OpenApiTypes.STR,
        },
    )
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            user_data = UserData.model_validate(data)
            locations = self.tracker.get_latest_location(
                location=user_data.location,
                zoom=user_data.zoom,
                map_width=user_data.width,
                map_height=user_data.height,
            )
            return Response(
                {"locations": [loc.model_dump() for loc in locations]},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                f"Invalid request data: {e}", status=status.HTTP_400_BAD_REQUEST
            )
