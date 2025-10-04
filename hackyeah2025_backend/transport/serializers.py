"""
Serializers for transport app
"""
from rest_framework import serializers
from transport.models import (
    Station, Route, RoutePoint, Journey,
    Report, ReportType, JourneyPassenger
)


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


class ReportTypeSerializer(serializers.ModelSerializer):
    """Serializer for ReportType model"""

    class Meta:
        model = ReportType
        fields = [
            'id',
            'name',
            'description',
            'severity',
            'icon',
            'color',
            'active',
        ]
        read_only_fields = ['id']


class ReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Report"""

    class Meta:
        model = Report
        fields = [
            'category',
            'delay_minutes',
            'description',
            'image',
            'confidence_level',
            'location_latitude',
            'location_longitude',
        ]
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True},
            'image': {'required': False, 'allow_null': True},
            'delay_minutes': {'required': False, 'allow_null': True},
            'confidence_level': {'required': False, 'default': 0.5},
            'location_latitude': {'required': False, 'allow_null': True},
            'location_longitude': {'required': False, 'allow_null': True},
        }

    def validate_category(self, value):
        """Validate that category is one of allowed choices"""
        allowed_categories = [choice[0] for choice in Report.CATEGORY_CHOICES]
        if value not in allowed_categories:
            raise serializers.ValidationError(f"Invalid category. Must be one of: {', '.join(allowed_categories)}")
        return value


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for Report model - read/list"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    report_type_name = serializers.CharField(source='report_type.name', read_only=True)
    from_station_name = serializers.CharField(source='from_station.name', read_only=True)
    to_station_name = serializers.CharField(source='to_station.name', read_only=True)
    route_name = serializers.CharField(source='route.name', read_only=True)
    route_line_number = serializers.CharField(source='route.line_number', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id',
            'user',
            'user_username',
            'journey',
            'route',
            'route_name',
            'route_line_number',
            'from_station',
            'from_station_name',
            'to_station',
            'to_station_name',
            'report_type',
            'report_type_name',
            'category',
            'category_display',
            'status',
            'status_display',
            'delay_minutes',
            'description',
            'image',
            'is_staff_report',
            'confidence_level',
            'location_latitude',
            'location_longitude',
            'created_at',
            'updated_at',
            'confirmed_at',
            'resolved_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'is_staff_report']


class JourneyPassengerSerializer(serializers.ModelSerializer):
    """Serializer for JourneyPassenger model"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    journey_info = JourneySerializer(source='journey', read_only=True)

    class Meta:
        model = JourneyPassenger
        fields = [
            'id',
            'user',
            'user_username',
            'journey',
            'journey_info',
            'boarded_at',
            'exited_at',
            'is_active',
        ]
        read_only_fields = ['id', 'boarded_at']
