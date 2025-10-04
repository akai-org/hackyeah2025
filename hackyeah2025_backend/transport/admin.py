from django.contrib import admin
from transport.models import (
    Carrier, Station, Track, Platform, Vehicle, Route, RoutePoint,
    StationType, UserProfile, ReportType, Report, UserReport, UserStats, Weather, Ticket,
    Journey, JourneyStatus, StationConnection, RouteGraph
)


@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ['name', 'priority', 'ticket_purchase_link', 'created_at']
    list_filter = ['priority', 'created_at']
    search_fields = ['name']
    ordering = ['-priority', 'name']


@admin.register(StationType)
class StationTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'location', 'platform_capacity', 'current_occupancy', 'latitude', 'longitude', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['name', 'location']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ['number', 'name', 'length_meters', 'parent_track', 'created_at']
    list_filter = ['created_at']
    search_fields = ['number', 'name']
    raw_id_fields = ['parent_track']


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ['station', 'number', 'track', 'max_wagons', 'active', 'created_at']
    list_filter = ['active', 'station', 'created_at']
    search_fields = ['number', 'station__name']
    raw_id_fields = ['station', 'track']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['identification_number', 'carrier', 'type', 'max_speed', 'average_speed', 'passenger_capacity', 'active']
    list_filter = ['type', 'active', 'carrier', 'created_at']
    search_fields = ['identification_number', 'carrier__name']
    raw_id_fields = ['carrier']


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['line_number', 'name', 'carrier', 'vehicle', 'active', 'created_at'
]
    list_filter = ['active', 'carrier', 'created_at']
    search_fields = ['line_number', 'name', 'carrier__name']
    raw_id_fields = ['carrier', 'vehicle']


@admin.register(RoutePoint)
class RoutePointAdmin(admin.ModelAdmin):
    list_display = ['route', 'sequence', 'station', 'platform', 'scheduled_arrival_time', 'scheduled_departure_time']
    list_filter = ['route', 'station']
    search_fields = ['route__line_number', 'station__name']
    ordering = ['route', 'sequence']
    raw_id_fields = ['route', 'station', 'platform', 'track']


class JourneyStatusInline(admin.TabularInline):
    model = JourneyStatus
    extra = 0
    readonly_fields = ['route_point', 'scheduled_arrival', 'scheduled_departure', 'actual_arrival', 'actual_departure', 'delay_minutes']
    fields = ['route_point', 'scheduled_arrival', 'actual_arrival', 'scheduled_departure', 'actual_departure', 'delay_minutes', 'platform_changed', 'actual_platform']


@admin.register(Journey)
class JourneyAdmin(admin.ModelAdmin):
    list_display = ['id', 'route', 'vehicle', 'journey_date', 'status', 'current_delay_minutes', 'current_station', 'next_station', 'scheduled_departure']
    list_filter = ['status', 'journey_date', 'route', 'vehicle']
    search_fields = ['route__line_number', 'vehicle__identification_number', 'current_station__name']
    raw_id_fields = ['route', 'vehicle', 'current_station', 'next_station']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'journey_date'
    inlines = [JourneyStatusInline]

    fieldsets = (
        ('Journey Information', {
            'fields': ('route', 'vehicle', 'journey_date', 'status')
        }),
        ('Schedule', {
            'fields': ('scheduled_departure', 'actual_departure', 'scheduled_arrival', 'actual_arrival')
        }),
        ('Current Status', {
            'fields': ('current_delay_minutes', 'current_station', 'next_station')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_delayed', 'mark_as_completed']

    def mark_as_delayed(self, request, queryset):
        updated = queryset.update(status='DELAYED')
        self.message_user(request, f"Marked {updated} journeys as delayed.")
    mark_as_delayed.short_description = "Mark selected journeys as delayed"

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='COMPLETED')
        self.message_user(request, f"Marked {updated} journeys as completed.")
    mark_as_completed.short_description = "Mark selected journeys as completed"


@admin.register(JourneyStatus)
class JourneyStatusAdmin(admin.ModelAdmin):
    list_display = ['journey', 'route_point', 'scheduled_arrival', 'actual_arrival', 'delay_minutes', 'platform_changed']
    list_filter = ['platform_changed', 'journey__journey_date', 'journey__route']
    search_fields = ['journey__route__line_number', 'route_point__station__name']
    raw_id_fields = ['journey', 'route_point', 'actual_platform']
    readonly_fields = ['updated_at']

    fieldsets = (
        ('Journey Information', {
            'fields': ('journey', 'route_point')
        }),
        ('Schedule', {
            'fields': ('scheduled_arrival', 'actual_arrival', 'scheduled_departure', 'actual_departure', 'delay_minutes')
        }),
        ('Platform', {
            'fields': ('platform_changed', 'actual_platform')
        }),
        ('Notes', {
            'fields': ('notes', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Weather)
class WeatherAdmin(admin.ModelAdmin):
    list_display = ['station', 'condition', 'temperature', 'speed_impact_percent', 'visibility_meters', 'recorded_at', 'valid_until']
    list_filter = ['condition', 'station', 'recorded_at']
    search_fields = ['station__name']
    raw_id_fields = ['station']
    readonly_fields = ['recorded_at']
    date_hierarchy = 'recorded_at'


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'user', 'route', 'vehicle', 'from_station', 'to_station', 'travel_date', 'status', 'price']
    list_filter = ['status', 'travel_date', 'route', 'purchase_date']
    search_fields = ['ticket_number', 'user__username', 'route__line_number', 'from_station__name', 'to_station__name']
    raw_id_fields = ['user', 'route', 'vehicle', 'from_station', 'to_station']
    readonly_fields = ['purchase_date']
    date_hierarchy = 'travel_date'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'date_of_birth', 'phone_number', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone_number']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ReportType)
class ReportTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'severity', 'color', 'icon', 'active', 'created_at']
    list_filter = ['severity', 'active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-severity', 'name']


class UserReportInline(admin.TabularInline):
    model = UserReport
    extra = 0
    readonly_fields = ['user', 'is_staff_report', 'confidence_level', 'delay_minutes', 'description', 'created_at']
    fields = ['user', 'is_staff_report', 'ticket', 'confidence_level', 'delay_minutes', 'description', 'created_at']
    can_delete = False


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'report_type', 'journey', 'route', 'from_station', 'to_station', 'status', 'user_reports_count', 'is_staff_reported', 'average_delay_minutes', 'created_at']
    list_filter = ['status', 'report_type', 'is_staff_reported', 'route', 'created_at']
    search_fields = ['description', 'route__line_number', 'from_station__name', 'to_station__name', 'journey__id']
    raw_id_fields = ['journey', 'route', 'from_station', 'to_station', 'report_type']
    readonly_fields = ['user_reports_count', 'is_staff_reported', 'average_delay_minutes', 'created_at', 'updated_at', 'confirmed_at']
    date_hierarchy = 'created_at'
    inlines = [UserReportInline]

    fieldsets = (
        ('Route Information', {
            'fields': ('journey', 'route', 'from_station', 'to_station', 'report_type')
        }),
        ('Status', {
            'fields': ('status', 'user_reports_count', 'is_staff_reported', 'average_delay_minutes')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_confirmed', 'mark_as_resolved']

    def mark_as_confirmed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='CONFIRMED', confirmed_at=timezone.now())
        self.message_user(request, f"Marked {updated} reports as confirmed.")
    mark_as_confirmed.short_description = "Mark selected reports as confirmed"

    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='RESOLVED', resolved_at=timezone.now())
        self.message_user(request, f"Marked {updated} reports as resolved.")
    mark_as_resolved.short_description = "Mark selected reports as resolved"


@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'is_staff_report', 'ticket', 'confidence_level', 'report', 'delay_minutes', 'weather_condition', 'created_at']
    list_filter = ['is_staff_report', 'report__status', 'report__report_type', 'created_at']
    search_fields = ['user__username', 'ticket__ticket_number', 'report__description', 'report__route__line_number', 'report__from_station__name', 'report__to_station__name']
    raw_id_fields = ['user', 'ticket', 'report']
    readonly_fields = ['created_at']

    fieldsets = (
        ('User and Ticket', {
            'fields': ('user', 'ticket')
        }),
        ('Report Details', {
            'fields': ('report', 'is_staff_report', 'confidence_level', 'delay_minutes', 'description', 'weather_condition')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(StationConnection)
class StationConnectionAdmin(admin.ModelAdmin):
    list_display = ['from_station', 'to_station', 'distance_km', 'estimated_time_minutes', 'is_bidirectional', 'max_speed_kmh', 'active', 'created_at']
    list_filter = ['is_bidirectional', 'active', 'created_at']
    search_fields = ['from_station__name', 'to_station__name']
    raw_id_fields = ['from_station', 'to_station']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Connection', {
            'fields': ('from_station', 'to_station', 'is_bidirectional')
        }),
        ('Details', {
            'fields': ('distance_km', 'estimated_time_minutes', 'max_speed_kmh', 'active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RouteGraph)
class RouteGraphAdmin(admin.ModelAdmin):
    list_display = ['route', 'sequence', 'from_station', 'to_station', 'scheduled_departure_from_first_station', 'scheduled_arrival_at_second_station']
    list_filter = ['route']
    search_fields = ['route__line_number', 'connection__from_station__name', 'connection__to_station__name']
    raw_id_fields = ['route', 'connection']
    ordering = ['route', 'sequence']

    fieldsets = (
        ('Route Information', {
            'fields': ('route', 'connection', 'sequence')
        }),
        ('Schedule', {
            'fields': ('scheduled_departure_from_first_station', 'scheduled_arrival_at_second_station')
        }),
    )
