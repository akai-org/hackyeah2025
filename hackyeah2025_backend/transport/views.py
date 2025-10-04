from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db.models import Sum
from datetime import datetime, timedelta

from transport.models import Station, Route, RoutePoint, Journey
from transport.serializers import StationSerializer, ConnectionSerializer


class StationListView(generics.ListAPIView):
    """
    API endpoint to retrieve all stations.

    Returns a list of all railway stations with their details including:
    - Name, location, and coordinates
    - Station type
    - Platform capacity and current occupancy
    - Capacity status
    """
    queryset = Station.objects.all().select_related('type')
    serializer_class = StationSerializer

    @extend_schema(
        summary="Get all stations",
        description="Retrieve a list of all railway stations with their complete information",
        responses={
            200: StationSerializer(many=True),
        },
        tags=['Stations']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ConnectionSearchView(APIView):
    """
    API endpoint to search for connections between two stations.

    Given start and end station IDs, returns available routes with:
    - Departure and arrival times
    - Travel duration
    - Distance and number of stops
    - Next scheduled journeys
    """

    @extend_schema(
        summary="Search connections between stations",
        description="Find all available routes between two stations with timing and journey information",
        parameters=[
            OpenApiParameter(
                name='from_station',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description='ID of the departure station'
            ),
            OpenApiParameter(
                name='to_station',
                type=OpenApiTypes.INT,
                required=True,
                location=OpenApiParameter.QUERY,
                description='ID of the arrival station'
            ),
        ],
        responses={
            200: ConnectionSerializer(many=True),
            400: {'description': 'Invalid parameters'},
            404: {'description': 'No connections found'},
        },
        tags=['Connections']
    )
    def get(self, request):
        validation_result = self._validate_parameters(request)
        if validation_result is not None:
            return validation_result

        from_station_id = int(request.query_params.get('from_station'))
        to_station_id = int(request.query_params.get('to_station'))

        stations_result = self._get_stations(from_station_id, to_station_id)
        if isinstance(stations_result, Response):
            return stations_result
        from_station, to_station = stations_result

        common_route_ids = self._find_common_routes(from_station_id, to_station_id)
        if not common_route_ids:
            return self._empty_response('No direct connections found between these stations')

        connections = self._build_connections(
            common_route_ids,
            from_station_id,
            to_station_id,
            from_station,
            to_station
        )

        if not connections:
            return self._empty_response('No valid connections found (routes may go in opposite direction)')

        connections.sort(key=lambda x: x['travel_time_minutes'])

        serializer = ConnectionSerializer(connections, many=True)
        return Response({
            'connections': serializer.data,
            'count': len(connections),
            'message': 'Connections found successfully'
        }, status=status.HTTP_200_OK)

    def _validate_parameters(self, request):
        from_station_id = request.query_params.get('from_station')
        to_station_id = request.query_params.get('to_station')

        if not from_station_id or not to_station_id:
            return Response(
                {'error': 'Both from_station and to_station parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            int(from_station_id)
            int(to_station_id)
        except ValueError:
            return Response(
                {'error': 'Station IDs must be integers'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return None

    def _get_stations(self, from_station_id, to_station_id):
        try:
            from_station = Station.objects.get(id=from_station_id)
            to_station = Station.objects.get(id=to_station_id)
            return from_station, to_station
        except Station.DoesNotExist:
            return Response(
                {'error': 'One or both stations not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def _find_common_routes(self, from_station_id, to_station_id):
        routes_with_from = RoutePoint.objects.filter(
            station_id=from_station_id
        ).values_list('route_id', flat=True)

        routes_with_to = RoutePoint.objects.filter(
            station_id=to_station_id
        ).values_list('route_id', flat=True)

        return set(routes_with_from) & set(routes_with_to)

    def _build_connections(self, common_route_ids, from_station_id, to_station_id,
                          from_station, to_station):
        connections = []

        for route_id in common_route_ids:
            connection = self._build_single_connection(
                route_id,
                from_station_id,
                to_station_id,
                from_station,
                to_station
            )
            if connection:
                connections.append(connection)

        return connections

    def _build_single_connection(self, route_id, from_station_id, to_station_id,
                                 from_station, to_station):
        route = Route.objects.select_related('carrier', 'vehicle').get(id=route_id)

        departure_point = RoutePoint.objects.filter(
            route_id=route_id,
            station_id=from_station_id
        ).first()

        arrival_point = RoutePoint.objects.filter(
            route_id=route_id,
            station_id=to_station_id
        ).first()

        # Validate route direction
        if not self._is_valid_route_direction(departure_point, arrival_point):
            return None

        # Calculate travel time
        travel_time = self._calculate_travel_time(
            departure_point.scheduled_departure_time,
            arrival_point.scheduled_arrival_time
        )

        route_points = self._get_route_points(route_id, departure_point.sequence, arrival_point.sequence)

        distance = self._calculate_distance(route_points, departure_point.sequence)

        next_journeys = self._get_next_journeys(route_id)

        return {
            'route': route,
            'departure_station': from_station,
            'arrival_station': to_station,
            'departure_time': departure_point.scheduled_departure_time,
            'arrival_time': arrival_point.scheduled_arrival_time,
            'travel_time_minutes': travel_time,
            'distance_km': distance,
            'stops_count': route_points.count() - 2,
            'route_points': list(route_points),
            'next_journeys': list(next_journeys),
        }

    def _is_valid_route_direction(self, departure_point, arrival_point):
        if not departure_point or not arrival_point:
            return False
        return departure_point.sequence < arrival_point.sequence

    def _calculate_travel_time(self, departure_time, arrival_time):
        dep_time = datetime.combine(datetime.today(), departure_time)
        arr_time = datetime.combine(datetime.today(), arrival_time)

        if arr_time < dep_time:
            arr_time += timedelta(days=1)

        return int((arr_time - dep_time).total_seconds() / 60)

    def _get_route_points(self, route_id, start_sequence, end_sequence):
        return RoutePoint.objects.filter(
            route_id=route_id,
            sequence__gte=start_sequence,
            sequence__lte=end_sequence
        ).select_related('station', 'platform').order_by('sequence')

    def _calculate_distance(self, route_points, start_sequence):
        distance = route_points.filter(
            sequence__gt=start_sequence
        ).aggregate(
            total=Sum('distance_from_previous_km')
        )['total']
        return distance or 0

    def _get_next_journeys(self, route_id):
        today = datetime.now().date()
        return Journey.objects.filter(
            route_id=route_id,
            journey_date__gte=today,
            status__in=['SCHEDULED', 'BOARDING', 'DELAYED']
        ).select_related('route', 'vehicle').order_by('scheduled_departure')[:5]

    def _empty_response(self, message):
        return Response({
            'connections': [],
            'count': 0,
            'message': message
        }, status=status.HTTP_200_OK)
