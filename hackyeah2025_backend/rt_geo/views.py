from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from rt_geo.models import UserData, GeoLocation
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
                name="latitude",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Geographical latitude of the center location for the map",
            ),
            OpenApiParameter(
                name="longitude",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Geographical longitude of the center location for the map",
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
            200: OpenApiResponse(
                description="Vehicle info response",
                response={
                    "type": "object",
                    "properties": {
                        "locations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "vehicle_id": {
                                        "type": "string",
                                        "example": "IC-2137",
                                    },
                                    "longitude": {"type": "number", "example": 19.94},
                                    "latitude": {"type": "number", "example": 50.06},
                                },
                            },
                        },
                    },
                },
            ),
            400: OpenApiTypes.STR,
        },
    )
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params

            latitude = float(data.get("latitude"))
            longitude = float(data.get("longitude"))
            location = GeoLocation(latitude=latitude, longitude=longitude)
            zoom = int(data.get("zoom"))
            width = int(data.get("map_width"))
            height = int(data.get("map_height"))

            locations = self.tracker.get_latest_location(
                location=location,
                zoom=zoom,
                map_width=width,
                map_height=height,
            )
            return Response(
                {"locations": locations},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                f"Invalid request data: {e}", status=status.HTTP_400_BAD_REQUEST
            )
