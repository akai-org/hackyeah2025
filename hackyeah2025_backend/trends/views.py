from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.http import HttpResponse, HttpRequest
from transport.models.route import Route
from transport.models.journey import Journey
from transport.models.report import Report
from hackyeah2025_backend.settings import LLM_API_KEY
import requests

TREND_PROMPT = """
Based on the following historical data, provide a summary of trends for the given route.
Please filter any inappropriate language from the reports, but keep their context intact.
Focus on key insights about the route's performance, safety, and any recurring issues.

The historical data will be formatted as follows:
Calculated average delay: {avg_delays} minutes

Report format: 
*TYPE* - One of the following types:
DELAY - Delay (train stopped or moving slowly
TECHNICAL_FAILURE - Technical failure (vehicle, signaling, switches
RANDOM_EVENT - Random event (accident, passenger illness
INFRASTRUCTURE - Infrastructure issues (track maintenance, blocked crossing
OVERCROWDING - Overcrowding (no seats, very crowded
WEATHER - Weather conditions (snow, storm, heat affecting operations
COMMUNITY_INFO - Community information (lost/found items, passenger assistance
OTHER - Other
*DESCRIPTION* - (optional) context provided by users
{reports}
"""


class TrendView(APIView):
    """
    API endpoint to retrieve trends for a given route using historical data.

    Returns a summary of trends including:
    - Average delays
    - Risk factor (amount of incidents reported as a percentage of all trips)
    - If there are any reoccuring events they will be mentioned
    """

    base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

    @extend_schema(
        summary="Get trends for a route",
        description="Retrieve trend data including average delays, risk factors, and reoccurring events for a specified route",
        parameters=[
            OpenApiParameter(
                name="route_name",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Name of the route to analyze",
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        tags=["Trends"],
    )
    def get(self, request: HttpRequest, *args, **kwargs):
        # Example static trend data
        data = request.GET

        # get all journeys for given route_name
        route_name = data.get("route_name")
        if not route_name:
            return Response(
                {"error": "Route name parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch the route object
        try:
            route = Route.objects.get(name=route_name)
            journeys = Journey.objects.filter(route=route)

            print(f"Found {journeys.count()} journeys for route {route_name}")
            print(f"Route details: {route}")
            print(f"Journey details: {journeys}")

            avg_delays = (
                sum(j.calculate_delay() for j in journeys) / len(journeys)
                if journeys
                else 0
            )

            reports = Report.objects.filter(
                journey__in=journeys, status="CONFIRMED", confidence_level__gte=0.6
            )

            formatted_reports = "\n".join(
                f"*{r.report_type}* - {r.description or 'No description'}"
                for r in reports
            )

            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": LLM_API_KEY,
            }

            requests.post(
                self.base_url,
                headers=headers,
                json={
                    "contents": [
                        {
                            "parts": {
                                "text": TREND_PROMPT.format(
                                    avg_delays=avg_delays,
                                    reports=formatted_reports,
                                ),
                            }
                        }
                    ]
                },
            )
        except Route.DoesNotExist:
            return Response(
                {"error": "No trends yet!"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return HttpResponse("Trends data placeholder", status=200)
