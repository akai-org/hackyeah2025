from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db.models import Sum
from datetime import datetime, timedelta

from transport.models import Station, Route, RoutePoint, Journey
from transport.serializers import (
    StationSerializer,
    ConnectionSerializer,
    ConnectionWithTransfersSerializer
)


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

        # First, try to find direct connections
        common_route_ids = self._find_common_routes(from_station_id, to_station_id)

        if common_route_ids:
            connections = self._build_connections(
                common_route_ids,
                from_station_id,
                to_station_id,
                from_station,
                to_station
            )

            if connections:
                connections.sort(key=lambda x: x['travel_time_minutes'])
                serializer = ConnectionSerializer(connections, many=True)
                return Response({
                    'direct_connections': serializer.data,
                    'connections_with_transfers': [],
                    'count': len(connections),
                    'message': 'Direct connections found successfully'
                }, status=status.HTTP_200_OK)

        # If no direct connections, search for connections with transfers (up to 3 trains)
        connections_with_transfers = self._find_connections_with_transfers(
            from_station_id,
            to_station_id,
            from_station,
            to_station,
            max_transfers=2  # 2 transfers = 3 trains total
        )

        if connections_with_transfers:
            # Sort by total time (travel + waiting)
            connections_with_transfers.sort(
                key=lambda x: x['total_travel_time_minutes'] + x['total_waiting_time_minutes']
            )
            serializer = ConnectionWithTransfersSerializer(connections_with_transfers, many=True)
            return Response({
                'direct_connections': [],
                'connections_with_transfers': serializer.data,
                'count': len(connections_with_transfers),
                'message': f'Found {len(connections_with_transfers)} connection(s) with transfers'
            }, status=status.HTTP_200_OK)

        return self._empty_response('No connections found between these stations')

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

    def _find_connections_with_transfers(self, from_station_id, to_station_id,
                                        from_station, to_station, max_transfers=2):
        """
        Find connections with transfers using BFS approach.
        max_transfers=2 means up to 3 trains (0, 1, or 2 transfers)
        """
        all_connections = []

        # Try to find connections with 1 transfer (2 trains)
        connections_1_transfer = self._find_connections_with_n_transfers(
            from_station_id, to_station_id, from_station, to_station, 1
        )
        all_connections.extend(connections_1_transfer)

        # Try to find connections with 2 transfers (3 trains)
        connections_2_transfers = self._find_connections_with_n_transfers(
            from_station_id, to_station_id, from_station, to_station, 2
        )
        all_connections.extend(connections_2_transfers)

        return all_connections

    def _find_connections_with_n_transfers(self, from_station_id, to_station_id,
                                          from_station, to_station, num_transfers):
        """Find connections with exactly n transfers"""
        connections = []

        if num_transfers == 1:
            # Find connections via 1 intermediate station (2 trains)
            connections = self._find_connections_via_one_transfer(
                from_station_id, to_station_id, from_station, to_station
            )
        elif num_transfers == 2:
            # Find connections via 2 intermediate stations (3 trains)
            connections = self._find_connections_via_two_transfers(
                from_station_id, to_station_id, from_station, to_station
            )

        return connections

    def _find_connections_via_one_transfer(self, from_station_id, to_station_id,
                                          from_station, to_station):
        """Find all connections with exactly 1 transfer"""
        connections = []

        # Get all routes from departure station
        routes_from_start = RoutePoint.objects.filter(
            station_id=from_station_id
        ).values_list('route_id', flat=True).distinct()

        # Get all routes to destination station
        routes_to_end = RoutePoint.objects.filter(
            station_id=to_station_id
        ).values_list('route_id', flat=True).distinct()

        # Find all possible intermediate stations
        for first_route_id in routes_from_start:
            # Get all stations on the first route after departure
            first_route_points = RoutePoint.objects.filter(
                route_id=first_route_id
            ).order_by('sequence')

            start_point = first_route_points.filter(station_id=from_station_id).first()
            if not start_point:
                continue

            # Get stations after the start point on this route
            intermediate_stations = first_route_points.filter(
                sequence__gt=start_point.sequence
            )

            for intermediate_point in intermediate_stations:
                intermediate_station_id = intermediate_point.station_id

                # Check if any second route goes from this intermediate station to destination
                for second_route_id in routes_to_end:
                    if second_route_id == first_route_id:
                        continue  # Skip same route

                    # Check if second route stops at intermediate station
                    second_route_points = RoutePoint.objects.filter(
                        route_id=second_route_id
                    ).order_by('sequence')

                    intermediate_on_second = second_route_points.filter(
                        station_id=intermediate_station_id
                    ).first()

                    end_point = second_route_points.filter(
                        station_id=to_station_id
                    ).first()

                    if intermediate_on_second and end_point:
                        # Validate direction on second route
                        if intermediate_on_second.sequence < end_point.sequence:
                            # Build the connection with transfer
                            connection = self._build_connection_with_transfer(
                                first_route_id, second_route_id,
                                from_station_id, intermediate_station_id, to_station_id,
                                from_station, to_station
                            )
                            if connection:
                                connections.append(connection)

        return connections

    def _find_connections_via_two_transfers(self, from_station_id, to_station_id,
                                           from_station, to_station):
        """Find all connections with exactly 2 transfers (3 trains)"""
        connections = []

        # Get all routes from departure station
        routes_from_start = RoutePoint.objects.filter(
            station_id=from_station_id
        ).values_list('route_id', flat=True).distinct()

        for first_route_id in routes_from_start:
            first_route_points = RoutePoint.objects.filter(
                route_id=first_route_id
            ).order_by('sequence')

            start_point = first_route_points.filter(station_id=from_station_id).first()
            if not start_point:
                continue

            # Get stations after the start point on first route
            first_intermediate_stations = first_route_points.filter(
                sequence__gt=start_point.sequence
            )

            for first_intermediate_point in first_intermediate_stations:
                first_transfer_id = first_intermediate_point.station_id

                # Find routes that pass through first transfer station (excluding first route)
                second_routes = RoutePoint.objects.filter(
                    station_id=first_transfer_id
                ).exclude(route_id=first_route_id).values_list('route_id', flat=True).distinct()

                for second_route_id in second_routes:
                    second_route_points = RoutePoint.objects.filter(
                        route_id=second_route_id
                    ).order_by('sequence')

                    first_transfer_on_second = second_route_points.filter(
                        station_id=first_transfer_id
                    ).first()

                    if not first_transfer_on_second:
                        continue

                    # Get stations after first transfer on second route
                    second_intermediate_stations = second_route_points.filter(
                        sequence__gt=first_transfer_on_second.sequence
                    )

                    for second_intermediate_point in second_intermediate_stations:
                        second_transfer_id = second_intermediate_point.station_id

                        if second_transfer_id == to_station_id:
                            continue  # Skip if this is the destination

                        # Find routes from second transfer to destination (excluding first two routes)
                        third_routes = RoutePoint.objects.filter(
                            station_id=second_transfer_id
                        ).exclude(
                            route_id__in=[first_route_id, second_route_id]
                        ).values_list('route_id', flat=True).distinct()

                        for third_route_id in third_routes:
                            third_route_points = RoutePoint.objects.filter(
                                route_id=third_route_id
                            ).order_by('sequence')

                            second_transfer_on_third = third_route_points.filter(
                                station_id=second_transfer_id
                            ).first()

                            end_point = third_route_points.filter(
                                station_id=to_station_id
                            ).first()

                            if second_transfer_on_third and end_point:
                                # Validate direction on third route
                                if second_transfer_on_third.sequence < end_point.sequence:
                                    # Build the connection with 2 transfers
                                    connection = self._build_connection_with_two_transfers(
                                        first_route_id, second_route_id, third_route_id,
                                        from_station_id, first_transfer_id, second_transfer_id, to_station_id,
                                        from_station, to_station
                                    )
                                    if connection:
                                        connections.append(connection)

        return connections

    def _build_connection_with_transfer(self, first_route_id, second_route_id,
                                       from_station_id, transfer_station_id, to_station_id,
                                       from_station, to_station):
        """Build a connection object with 1 transfer"""
        try:
            # Get stations
            transfer_station = Station.objects.get(id=transfer_station_id)

            # Build first segment
            first_segment = self._build_segment(
                first_route_id, from_station_id, transfer_station_id,
                from_station, transfer_station
            )

            if not first_segment:
                return None

            # Build second segment
            second_segment = self._build_segment(
                second_route_id, transfer_station_id, to_station_id,
                transfer_station, to_station
            )

            if not second_segment:
                return None

            # Calculate waiting time at transfer station
            waiting_time = self._calculate_travel_time(
                first_segment['arrival_time'],
                second_segment['departure_time']
            )

            # If negative waiting time, the connection is not possible
            if waiting_time < 0:
                waiting_time += 24 * 60  # Add 24 hours if it's next day

            # Add transfer info to second segment
            second_segment['transfer_station'] = transfer_station
            second_segment['waiting_time_minutes'] = waiting_time

            # Calculate totals
            total_travel_time = (first_segment['travel_time_minutes'] +
                               second_segment['travel_time_minutes'])
            total_distance = (first_segment['distance_km'] +
                            second_segment['distance_km'])
            total_stops = (first_segment['stops_count'] +
                         second_segment['stops_count'])

            return {
                'segments': [first_segment, second_segment],
                'total_travel_time_minutes': total_travel_time,
                'total_waiting_time_minutes': waiting_time,
                'total_distance_km': total_distance,
                'total_stops_count': total_stops,
                'transfers_count': 1,
                'departure_station': from_station,
                'arrival_station': to_station,
                'departure_time': first_segment['departure_time'],
                'arrival_time': second_segment['arrival_time'],
            }
        except Exception as e:
            return None

    def _build_connection_with_two_transfers(self, first_route_id, second_route_id, third_route_id,
                                            from_station_id, first_transfer_id, second_transfer_id, to_station_id,
                                            from_station, to_station):
        """Build a connection object with 2 transfers"""
        try:
            # Get transfer stations
            first_transfer_station = Station.objects.get(id=first_transfer_id)
            second_transfer_station = Station.objects.get(id=second_transfer_id)

            # Build three segments
            first_segment = self._build_segment(
                first_route_id, from_station_id, first_transfer_id,
                from_station, first_transfer_station
            )

            if not first_segment:
                return None

            second_segment = self._build_segment(
                second_route_id, first_transfer_id, second_transfer_id,
                first_transfer_station, second_transfer_station
            )

            if not second_segment:
                return None

            third_segment = self._build_segment(
                third_route_id, second_transfer_id, to_station_id,
                second_transfer_station, to_station
            )

            if not third_segment:
                return None

            # Calculate waiting times at transfer stations
            first_waiting_time = self._calculate_travel_time(
                first_segment['arrival_time'],
                second_segment['departure_time']
            )

            if first_waiting_time < 0:
                first_waiting_time += 24 * 60

            second_waiting_time = self._calculate_travel_time(
                second_segment['arrival_time'],
                third_segment['departure_time']
            )

            if second_waiting_time < 0:
                second_waiting_time += 24 * 60

            # Add transfer info to segments
            second_segment['transfer_station'] = first_transfer_station
            second_segment['waiting_time_minutes'] = first_waiting_time

            third_segment['transfer_station'] = second_transfer_station
            third_segment['waiting_time_minutes'] = second_waiting_time

            # Calculate totals
            total_travel_time = (first_segment['travel_time_minutes'] +
                               second_segment['travel_time_minutes'] +
                               third_segment['travel_time_minutes'])
            total_waiting_time = first_waiting_time + second_waiting_time
            total_distance = (first_segment['distance_km'] +
                            second_segment['distance_km'] +
                            third_segment['distance_km'])
            total_stops = (first_segment['stops_count'] +
                         second_segment['stops_count'] +
                         third_segment['stops_count'])

            return {
                'segments': [first_segment, second_segment, third_segment],
                'total_travel_time_minutes': total_travel_time,
                'total_waiting_time_minutes': total_waiting_time,
                'total_distance_km': total_distance,
                'total_stops_count': total_stops,
                'transfers_count': 2,
                'departure_station': from_station,
                'arrival_station': to_station,
                'departure_time': first_segment['departure_time'],
                'arrival_time': third_segment['arrival_time'],
            }
        except Exception as e:
            return None

    def _build_segment(self, route_id, from_station_id, to_station_id,
                      from_station, to_station):
        """Build a single segment of a journey"""
        try:
            route = Route.objects.select_related('carrier', 'vehicle').get(id=route_id)

            departure_point = RoutePoint.objects.filter(
                route_id=route_id,
                station_id=from_station_id
            ).first()

            arrival_point = RoutePoint.objects.filter(
                route_id=route_id,
                station_id=to_station_id
            ).first()

            if not self._is_valid_route_direction(departure_point, arrival_point):
                return None

            travel_time = self._calculate_travel_time(
                departure_point.scheduled_departure_time,
                arrival_point.scheduled_arrival_time
            )

            route_points = self._get_route_points(
                route_id, departure_point.sequence, arrival_point.sequence
            )

            distance = self._calculate_distance(route_points, departure_point.sequence)

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
                'transfer_station': None,
                'waiting_time_minutes': None,
            }
        except Exception as e:
            return None
