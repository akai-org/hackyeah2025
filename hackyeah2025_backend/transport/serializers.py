"""
Serializers for transport app
"""
from rest_framework import serializers
from transport.models import Station, Route, RoutePoint, Journey


class StationSerializer(serializers.ModelSerializer):
    """Serializer for Station model"""

    is_at_capacity = serializers.ReadOnlyField()
    type_name = serializers.CharField(source='type.name', read_only=True, allow_null=True)

    class Meta:
        model = Station
        fields = [
            'id',
            'name',
            'location',
            'latitude',
            'longitude',
            'type',
            'type_name',
            'platform_capacity',
            'current_occupancy',
            'is_at_capacity',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RoutePointSerializer(serializers.ModelSerializer):
    """Serializer for RoutePoint model"""
    station_name = serializers.CharField(source='station.name', read_only=True)
    platform_name = serializers.CharField(source='platform.name', read_only=True, allow_null=True)

    class Meta:
        model = RoutePoint
        fields = [
            'id',
            'station',
            'station_name',
            'platform',
            'platform_name',
            'sequence',
            'scheduled_arrival_time',
            'scheduled_departure_time',
            'stop_duration_minutes',
            'distance_from_previous_km',
        ]


class RouteSerializer(serializers.ModelSerializer):
    """Serializer for Route model"""
    carrier_name = serializers.CharField(source='carrier.name', read_only=True)
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True, allow_null=True)

    class Meta:
        model = Route
        fields = [
            'id',
            'name',
            'line_number',
            'carrier',
            'carrier_name',
            'vehicle',
            'vehicle_name',
            'active',
            'created_at',
            'updated_at',
        ]


class JourneySerializer(serializers.ModelSerializer):
    """Serializer for Journey model"""
    route_info = RouteSerializer(source='route', read_only=True)
    start_station = serializers.SerializerMethodField()
    end_station = serializers.SerializerMethodField()

    class Meta:
        model = Journey
        fields = [
            'id',
            'route',
            'route_info',
            'journey_date',
            'scheduled_departure',
            'actual_departure',
            'scheduled_arrival',
            'actual_arrival',
            'status',
            'current_delay_minutes',
            'start_station',
            'end_station',
        ]

    def get_start_station(self, obj):
        station = obj.start_station
        return {'id': station.id, 'name': station.name} if station else None

    def get_end_station(self, obj):
        station = obj.end_station
        return {'id': station.id, 'name': station.name} if station else None


class ConnectionSerializer(serializers.Serializer):
    """Serializer for connection search results"""
    route = RouteSerializer(read_only=True)
    departure_station = StationSerializer(read_only=True)
    arrival_station = StationSerializer(read_only=True)
    departure_time = serializers.TimeField(read_only=True)
    arrival_time = serializers.TimeField(read_only=True)
    travel_time_minutes = serializers.IntegerField(read_only=True)
    distance_km = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    stops_count = serializers.IntegerField(read_only=True)
    route_points = RoutePointSerializer(many=True, read_only=True)
    next_journeys = JourneySerializer(many=True, read_only=True)
