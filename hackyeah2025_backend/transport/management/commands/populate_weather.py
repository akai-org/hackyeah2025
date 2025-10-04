from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from transport.models import Station, Weather


class Command(BaseCommand):
    help = 'Populate database with random weather conditions for Polish stations'

    def handle(self, *args, **kwargs):
        stations = Station.objects.all()

        if not stations.exists():
            self.stdout.write(self.style.ERROR('No stations found. Please run populate_stations first.'))
            return

        # Warunki pogodowe z prawdopodobieństwami (suma = 100)
        weather_distribution = [
            ('CLEAR', 40, 0, 15, 25),      # (typ, prawdopodobieństwo, wpływ na prędkość, temp_min, temp_max)
            ('RAIN', 25, -10, 5, 18),
            ('FOG', 15, -15, 0, 12),
            ('SNOW', 8, -25, -10, 2),
            ('WIND', 7, -8, 5, 20),
            ('STORM', 3, -30, 8, 22),
            ('ICE', 1, -40, -15, -2),
            ('EXTREME', 1, -50, -20, 0),
        ]

        created_count = 0
        updated_count = 0

        # Usuń stare wpisy pogodowe
        Weather.objects.all().delete()
        self.stdout.write(self.style.WARNING('Cleared old weather data'))

        for station in stations:
            # Losuj warunek pogodowy na podstawie prawdopodobieństwa
            rand = random.randint(1, 100)
            cumulative = 0
            selected_weather = None

            for weather_type, probability, speed_impact, temp_min, temp_max in weather_distribution:
                cumulative += probability
                if rand <= cumulative:
                    selected_weather = (weather_type, speed_impact, temp_min, temp_max)
                    break

            if not selected_weather:
                selected_weather = ('CLEAR', 0, 15, 25)

            weather_type, speed_impact, temp_min, temp_max = selected_weather

            # Losowa temperatura w zakresie dla danego warunku
            temperature = round(random.uniform(temp_min, temp_max), 1)

            # Losowa widoczność (w metrach)
            if weather_type == 'FOG':
                visibility = random.randint(50, 500)
            elif weather_type in ['RAIN', 'SNOW', 'STORM']:
                visibility = random.randint(500, 2000)
            elif weather_type == 'CLEAR':
                visibility = random.randint(8000, 15000)
            else:
                visibility = random.randint(2000, 8000)

            # Dodaj małą losową wariancję do wpływu na prędkość
            speed_impact_actual = speed_impact + random.randint(-3, 3)
            speed_impact_actual = max(-50, min(0, speed_impact_actual))  # Ogranicz do -50..0

            # Ważność prognozy: 3-8 godzin od teraz
            valid_hours = random.randint(3, 8)
            valid_until = timezone.now() + timedelta(hours=valid_hours)

            try:
                weather = Weather.objects.create(
                    station=station,
                    condition=weather_type,
                    temperature=temperature,
                    speed_impact_percent=speed_impact_actual,
                    visibility_meters=visibility,
                    valid_until=valid_until
                )
                created_count += 1

                # Wyświetl kolorowy output w zależności od warunków
                if weather_type in ['CLEAR', 'WIND']:
                    style = self.style.SUCCESS
                    icon = '☀️' if weather_type == 'CLEAR' else '💨'
                elif weather_type in ['RAIN', 'FOG']:
                    style = self.style.WARNING
                    icon = '🌧️' if weather_type == 'RAIN' else '🌫️'
                else:
                    style = self.style.ERROR
                    icon = '❄️' if weather_type == 'SNOW' else '⚠️'

                self.stdout.write(
                    style(f'{icon} {station.name}: {weather.get_condition_display()} '
                          f'({temperature}°C, visibility: {visibility}m, speed impact: {speed_impact_actual}%)')
                )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error creating weather for {station.name}: {str(e)}'))
                continue

        self.stdout.write(self.style.SUCCESS(f'\n=== Summary ==='))
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count} weather conditions'))
        self.stdout.write(self.style.SUCCESS(f'For: {stations.count()} stations'))

        # Statystyki pogody
        weather_stats = {}
        for weather_type, _, _, _, _ in weather_distribution:
            count = Weather.objects.filter(condition=weather_type).count()
            if count > 0:
                weather_stats[weather_type] = count

        self.stdout.write(self.style.SUCCESS(f'\nWeather distribution:'))
        for weather_type, count in sorted(weather_stats.items(), key=lambda x: -x[1]):
            self.stdout.write(f'  {weather_type}: {count} stations')
