from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db import transaction

from transport.models import (
    Report, ReportType, JourneyPassenger,
    Station, Route, Journey
)
from transport.serializers import (
    ReportCreateSerializer, ReportSerializer, ReportTypeSerializer
)


class CreateReportView(APIView):
    """
    API endpoint for creating reports about issues during journey.

    Requirements:
    - User must be authenticated
    - User must be an active passenger (JourneyPassenger with is_active=True)
    - Allows reporting delays, technical failures, overcrowding, etc.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create a report",
        description=(
            "Create a new report about an issue during your current journey. "
            "You must be an active passenger to submit a report. "
            "Available categories: DELAY, TECHNICAL_FAILURE, RANDOM_EVENT, "
            "INFRASTRUCTURE, OVERCROWDING, WEATHER, COMMUNITY_INFO, OTHER"
        ),
        request=ReportCreateSerializer,
        responses={
            201: ReportSerializer,
            400: {"description": "Bad request - validation errors"},
            403: {"description": "User is not an active passenger on any journey"},
            404: {"description": "Report type or stations not found"},
        },
        parameters=[
            OpenApiParameter(
                name='report_type_id',
                description='ID of the report type',
                required=True,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name='from_station_id',
                description='ID of the station where issue started',
                required=True,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name='to_station_id',
                description='ID of the station where issue ends/continues',
                required=True,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY
            ),
        ],
        tags=['Reports']
    )
    def post(self, request):
        """Create a new report"""
        user = request.user

        try:
            journey_passenger = JourneyPassenger.objects.select_related(
                'journey', 'journey__route'
            ).get(user=user, is_active=True)
        except JourneyPassenger.DoesNotExist:
            return Response(
                {
                    "error": "You must be an active passenger on a journey to submit a report.",
                    "detail": "Please board a journey first before reporting issues."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        report_type_id = request.query_params.get('report_type_id')
        from_station_id = request.query_params.get('from_station_id')
        to_station_id = request.query_params.get('to_station_id')

        if not all([report_type_id, from_station_id, to_station_id]):
            return Response(
                {
                    "error": "Missing required parameters",
                    "detail": "report_type_id, from_station_id, and to_station_id are required in query parameters"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ReportCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            report_type = ReportType.objects.get(id=report_type_id, active=True)
        except ReportType.DoesNotExist:
            return Response(
                {"error": f"Report type with id {report_type_id} not found or is not active"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            from_station = Station.objects.get(id=from_station_id)
            to_station = Station.objects.get(id=to_station_id)
        except Station.DoesNotExist:
            return Response(
                {"error": "One or both stations not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        journey = journey_passenger.journey
        route = journey.route

        with transaction.atomic():
            report = Report.objects.create(
                user=user,
                journey_passenger=journey_passenger,
                journey=journey,
                route=route,
                from_station=from_station,
                to_station=to_station,
                report_type=report_type,
                category=serializer.validated_data.get('category'),
                status='PENDING',
                delay_minutes=serializer.validated_data.get('delay_minutes'),
                description=serializer.validated_data.get('description', ''),
                image=serializer.validated_data.get('image'),
                confidence_level=serializer.validated_data.get('confidence_level', 0.5),
                location_latitude=serializer.validated_data.get('location_latitude'),
                location_longitude=serializer.validated_data.get('location_longitude'),
            )

            # is_staff_report jest ustawiany automatycznie w modelu przez save()

        response_serializer = ReportSerializer(report)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ReportTypeListView(generics.ListAPIView):
    """
    API endpoint to retrieve all active report types.

    Returns available report types with their severity, icon, and color
    for frontend display.
    """
    queryset = ReportType.objects.filter(active=True)
    serializer_class = ReportTypeSerializer

    @extend_schema(
        summary="Get all active report types",
        description="Retrieve a list of all active report types that users can use when submitting reports",
        responses={
            200: ReportTypeSerializer(many=True),
        },
        tags=['Reports']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserReportListView(generics.ListAPIView):
    """
    API endpoint to retrieve user's own reports.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ReportSerializer

    @extend_schema(
        summary="Get user's reports",
        description="Retrieve all reports submitted by the authenticated user",
        responses={
            200: ReportSerializer(many=True),
        },
        tags=['Reports']
    )
    def get_queryset(self):
        return Report.objects.filter(
            user=self.request.user
        ).select_related(
            'report_type', 'user', 'journey_passenger', 'journey', 'route',
            'from_station', 'to_station'
        ).order_by('-created_at')


class ReportListView(generics.ListAPIView):
    """
    API endpoint to retrieve all reports.

    Can be filtered by journey, route, or status.
    """
    serializer_class = ReportSerializer

    @extend_schema(
        summary="Get all reports",
        description="Retrieve all reports with optional filtering by journey, route, or status",
        parameters=[
            OpenApiParameter(
                name='journey_id',
                description='Filter by journey ID',
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name='route_id',
                description='Filter by route ID',
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name='status',
                description='Filter by status (PENDING, CONFIRMED, REJECTED, RESOLVED)',
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY
            ),
        ],
        responses={
            200: ReportSerializer(many=True),
        },
        tags=['Reports']
    )
    def get_queryset(self):
        queryset = Report.objects.select_related(
            'journey', 'route', 'from_station', 'to_station', 'report_type', 'user'
        ).order_by('-created_at')

        journey_id = self.request.query_params.get('journey_id')
        if journey_id:
            queryset = queryset.filter(journey_id=journey_id)

        route_id = self.request.query_params.get('route_id')
        if route_id:
            queryset = queryset.filter(route_id=route_id)

        report_status = self.request.query_params.get('status')
        if report_status:
            queryset = queryset.filter(status=report_status)

        return queryset
