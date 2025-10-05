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

        # Get stations by name (more reliable after fresh database)
        try:
            warszawa = Station.objects.get(name='Warszawa Centralna')
            krakow = Station.objects.get(name='Kraków Główny')
            wroclaw = Station.objects.get(name='Wrocław Główny')
            poznan = Station.objects.get(name='Poznań Główny')
            gdansk = Station.objects.get(name='Gdańsk Główny')
            katowice = Station.objects.get(name='Katowice')
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

        # Create multiple journeys throughout the day (every 1-2.5 hours)
        # For the next 7 days
        today = date.today()

        # Define departure times for each route (multiple trains per day)
        route_schedules = {
            route1: [
                time(5, 30), time(7, 0), time(8, 30), time(10, 15),
                time(12, 0), time(14, 30), time(16, 45), time(19, 0), time(21, 15)
            ],
            route2: [
                time(6, 0), time(8, 15), time(10, 0), time(12, 30),
                time(14, 0), time(16, 15), time(18, 30), time(20, 0), time(22, 15)
            ],
            route3: [
                time(5, 45), time(7, 30), time(9, 0), time(11, 15),
                time(13, 30), time(15, 45), time(18, 0), time(20, 30)
            ],
            route4: [
                time(6, 30), time(8, 0), time(10, 0), time(12, 15),
                time(14, 30), time(17, 0), time(19, 15), time(21, 30)
            ],
        }

        journeys_created = 0
        for day_offset in range(7):  # Next 7 days
            journey_date = today + timedelta(days=day_offset)

            for route, departure_times in route_schedules.items():
                first_point = route.route_points.order_by('sequence').first()
                last_point = route.route_points.order_by('-sequence').first()

                if not first_point or not last_point:
                    continue

                for departure_time in departure_times:
                    # Calculate arrival time based on route duration
                    departure_dt = datetime.combine(journey_date, departure_time)

                    # Calculate duration from route points
                    first_time = first_point.scheduled_departure_time
                    last_time = last_point.scheduled_arrival_time

                    # Handle time difference (might cross midnight)
                    if last_time < first_time:
                        duration = timedelta(
                            hours=24 - first_time.hour + last_time.hour,
                            minutes=last_time.minute - first_time.minute
                        )
                    else:
                        duration = timedelta(
                            hours=last_time.hour - first_time.hour,
                            minutes=last_time.minute - first_time.minute
                        )

                    arrival_dt = departure_dt + duration

                    # Random small delay or on-time
                    import random
                    delay = random.choice([0, 0, 0, 0, 5, 10, 15])  # Mostly on time

                    journey, created = Journey.objects.get_or_create(
                        route=route,
                        journey_date=journey_date,
                        scheduled_departure=departure_dt,
                        defaults={
                            'vehicle': vehicle,
                            'scheduled_arrival': arrival_dt,
                            'status': 'SCHEDULED',
                            'current_delay_minutes': delay
                        }
                    )

                    if created:
                        journeys_created += 1

        self.stdout.write(self.style.SUCCESS('Test routes created successfully!'))
        self.stdout.write(f'Total routes: {Route.objects.count()}')
        self.stdout.write(f'Total route points: {RoutePoint.objects.count()}')
        self.stdout.write(f'Total journeys created: {journeys_created}')
        self.stdout.write(f'Total journeys in DB: {Journey.objects.count()}')
