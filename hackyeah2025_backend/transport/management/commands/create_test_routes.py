"""
Management command to create test routes and connections
"""
from django.core.management.base import BaseCommand
from transport.models import Station, Route, RoutePoint, Journey, Carrier, Vehicle
from datetime import datetime, date, timedelta, time


class Command(BaseCommand):
    help = 'Create test routes with connections between stations'

    def handle(self, *args, **options):
        self.stdout.write('Creating test routes...')

        # Get carrier
        carrier = Carrier.objects.first()
        if not carrier:
            self.stdout.write(self.style.ERROR('No carriers found in database'))
            return

        # Get or create vehicle
        vehicle, created = Vehicle.objects.get_or_create(
            identification_number='TEST-001',
            defaults={
                'carrier': carrier,
                'type': 'TRAIN',
                'max_speed': 160.00,
                'average_speed': 120.00,
                'passenger_capacity': 400,
                'active': True
            }
        )

        # Get stations by ID (more reliable than names)
        try:
            warszawa = Station.objects.get(id=1)  # Warszawa Centralna
            krakow = Station.objects.get(id=2)     # Kraków
            wroclaw = Station.objects.get(id=3)    # Wrocław
            poznan = Station.objects.get(id=4)     # Poznań
            gdansk = Station.objects.get(id=5)     # Gdańsk
            katowice = Station.objects.get(id=7)   # Katowice
        except Station.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'Station not found: {e}'))
            return

        # Create Route 1: Warszawa -> Kraków
        route1, created = Route.objects.get_or_create(
            line_number='IC 1001',
            defaults={
                'name': 'Warszawa - Kraków',
                'carrier': carrier,
                'vehicle': vehicle,
                'active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created route: {route1.line_number}'))

        # Create route points for Route 1
        RoutePoint.objects.get_or_create(
            route=route1,
            station=warszawa,
            sequence=1,
            defaults={
                'scheduled_arrival_time': time(8, 0),
                'scheduled_departure_time': time(8, 0),
                'stop_duration_minutes': 0,
                'distance_from_previous_km': 0
            }
        )

        RoutePoint.objects.get_or_create(
            route=route1,
            station=katowice,
            sequence=2,
            defaults={
                'scheduled_arrival_time': time(10, 30),
                'scheduled_departure_time': time(10, 35),
                'stop_duration_minutes': 5,
                'distance_from_previous_km': 280
            }
        )

        RoutePoint.objects.get_or_create(
            route=route1,
            station=krakow,
            sequence=3,
            defaults={
                'scheduled_arrival_time': time(11, 30),
                'scheduled_departure_time': time(11, 30),
                'stop_duration_minutes': 0,
                'distance_from_previous_km': 90
            }
        )

        # Create Route 2: Kraków -> Warszawa (opposite direction)
        route2, created = Route.objects.get_or_create(
            line_number='IC 1002',
            defaults={
                'name': 'Kraków - Warszawa',
                'carrier': carrier,
                'vehicle': vehicle,
                'active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created route: {route2.line_number}'))

        RoutePoint.objects.get_or_create(
            route=route2,
            station=krakow,
            sequence=1,
            defaults={
                'scheduled_arrival_time': time(14, 0),
                'scheduled_departure_time': time(14, 0),
                'stop_duration_minutes': 0,
                'distance_from_previous_km': 0
            }
        )

        RoutePoint.objects.get_or_create(
            route=route2,
            station=katowice,
            sequence=2,
            defaults={
                'scheduled_arrival_time': time(15, 0),
                'scheduled_departure_time': time(15, 5),
                'stop_duration_minutes': 5,
                'distance_from_previous_km': 90
            }
        )

        RoutePoint.objects.get_or_create(
            route=route2,
            station=warszawa,
            sequence=3,
            defaults={
                'scheduled_arrival_time': time(17, 30),
                'scheduled_departure_time': time(17, 30),
                'stop_duration_minutes': 0,
                'distance_from_previous_km': 280
            }
        )

        # Create Route 3: Warszawa -> Gdańsk
        route3, created = Route.objects.get_or_create(
            line_number='IC 2001',
            defaults={
                'name': 'Warszawa - Gdańsk',
                'carrier': carrier,
                'vehicle': vehicle,
                'active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created route: {route3.line_number}'))

        RoutePoint.objects.get_or_create(
            route=route3,
            station=warszawa,
            sequence=1,
            defaults={
                'scheduled_arrival_time': time(9, 0),
                'scheduled_departure_time': time(9, 0),
                'stop_duration_minutes': 0,
                'distance_from_previous_km': 0
            }
        )

        RoutePoint.objects.get_or_create(
            route=route3,
            station=gdansk,
            sequence=2,
            defaults={
                'scheduled_arrival_time': time(12, 30),
                'scheduled_departure_time': time(12, 30),
                'stop_duration_minutes': 0,
                'distance_from_previous_km': 340
            }
        )

        # Create Route 4: Poznań -> Warszawa
        route4, created = Route.objects.get_or_create(
            line_number='IC 3001',
            defaults={
                'name': 'Poznań - Warszawa',
                'carrier': carrier,
                'vehicle': vehicle,
                'active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created route: {route4.line_number}'))

        RoutePoint.objects.get_or_create(
            route=route4,
            station=poznan,
            sequence=1,
            defaults={
                'scheduled_arrival_time': time(10, 0),
                'scheduled_departure_time': time(10, 0),
                'stop_duration_minutes': 0,
                'distance_from_previous_km': 0
            }
        )

        RoutePoint.objects.get_or_create(
            route=route4,
            station=warszawa,
            sequence=2,
            defaults={
                'scheduled_arrival_time': time(13, 0),
                'scheduled_departure_time': time(13, 0),
                'stop_duration_minutes': 0,
                'distance_from_previous_km': 310
            }
        )

        # Create some journeys for today and tomorrow
        today = date.today()
        tomorrow = today + timedelta(days=1)

        for route in [route1, route2, route3, route4]:
            first_point = route.route_points.order_by('sequence').first()
            last_point = route.route_points.order_by('-sequence').first()

            if first_point and last_point:
                # Create journey for today
                Journey.objects.get_or_create(
                    route=route,
                    journey_date=today,
                    defaults={
                        'vehicle': vehicle,
                        'scheduled_departure': datetime.combine(today, first_point.scheduled_departure_time),
                        'scheduled_arrival': datetime.combine(today, last_point.scheduled_arrival_time),
                        'status': 'SCHEDULED',
                        'current_delay_minutes': 0
                    }
                )

                # Create journey for tomorrow
                Journey.objects.get_or_create(
                    route=route,
                    journey_date=tomorrow,
                    defaults={
                        'vehicle': vehicle,
                        'scheduled_departure': datetime.combine(tomorrow, first_point.scheduled_departure_time),
                        'scheduled_arrival': datetime.combine(tomorrow, last_point.scheduled_arrival_time),
                        'status': 'SCHEDULED',
                        'current_delay_minutes': 0
                    }
                )

        self.stdout.write(self.style.SUCCESS('Test routes created successfully!'))
        self.stdout.write(f'Total routes: {Route.objects.count()}')
        self.stdout.write(f'Total route points: {RoutePoint.objects.count()}')
        self.stdout.write(f'Total journeys: {Journey.objects.count()}')
