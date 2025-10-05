from django.core.management.base import BaseCommand
from transport.models import Station, StationConnection
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create realistic station connections (graph edges) for Polish railway network'

    def handle(self, *args, **kwargs):
        # Pobierz stacje z bazy - używamy dokładnych nazw bez upraszczania
        stations = {}
        for station in Station.objects.all():
            stations[station.name] = station

        # Realistyczne połączenia kolejowe w Polsce z odległościami i czasami
        # UWAGA: Nazwy stacji mają błędne kodowanie polskich znaków (ó→w, ą→wna, ę→wne, itp.)
        connections_data = [
            # Magistrala CMK (Centralna Magistrala Kolejowa) - Warszawa - Katowice - Kraków
            ('Warszawa Centralna', 'Częstochowa', 221, 90, 160),
            ('Częstochowa', 'Katowice', 83, 45, 140),
            ('Katowice', 'Kraków Główny', 79, 50, 140),

            # Warszawa - Kraków przez Radom, Kielce
            ('Warszawa Centralna', 'Radom', 102, 75, 120),
            ('Radom', 'Kielce', 89, 70, 110),
            ('Kielce', 'Kraków Główny', 101, 85, 120),

            # Warszawa - Gdańsk
            ('Warszawa Centralna', 'Toruń Główny', 190, 120, 140),
            ('Toruń Główny', 'Bydgoszcz Główna', 45, 30, 120),
            ('Bydgoszcz Główna', 'Gdańsk Główny', 143, 90, 140),

            # Trójmiasto
            ('Gdańsk Główny', 'Sopot', 11, 12, 120),
            ('Sopot', 'Gdynia Główna', 8, 10, 120),

            # Warszawa - Poznań
            ('Warszawa Centralna', 'Konin', 155, 100, 140),
            ('Konin', 'Poznań Główny', 97, 65, 140),

            # Warszawa - Białystok
            ('Warszawa Centralna', 'Siedlce', 90, 60, 120),
            ('Siedlce', 'Białystok', 115, 80, 120),

            # Warszawa - Lublin
            ('Warszawa Centralna', 'Lublin', 170, 110, 140),

            # Warszawa - Łódź
            ('Warszawa Centralna', 'Łódź Fabryczna', 135, 75, 160),

            # Kraków - Zakopane (przez beskidy)
            ('Kraków Główny', 'Sucha Beskidzka', 62, 65, 100),
            ('Sucha Beskidzka', 'Rabka-Zdrój', 18, 25, 80),
            ('Kraków Główny', 'Tarnów', 82, 60, 120),
            ('Tarnów', 'Nowy Sącz', 63, 55, 100),

            # Kraków - Rzeszów
            ('Kraków Główny', 'Rzeszów Główny', 97, 75, 120),

            # Wrocław - Poznań
            ('Wrocław Główny', 'Poznań Główny', 170, 110, 140),

            # Wrocław - Warszawa
            ('Wrocław Główny', 'Łódź Fabryczna', 190, 120, 140),
            ('Łódź Fabryczna', 'Warszawa Centralna', 135, 75, 160),

            # Wrocław - Opole - Katowice
            ('Wrocław Główny', 'Opole Główne', 75, 50, 120),
            ('Opole Główne', 'Katowice', 92, 60, 120),

            # Śląsk
            ('Katowice', 'Gliwice', 25, 20, 100),
            ('Gliwice', 'Zabrze', 8, 10, 80),
            ('Katowice', 'Tychy', 24, 25, 100),
            ('Katowice', 'Jaworzno Szczakowa', 28, 25, 100),

            # Poznań - Szczecin
            ('Poznań Główny', 'Piła Główna', 80, 55, 120),
            ('Piła Główna', 'Stargard', 90, 65, 120),
            ('Stargard', 'Szczecin Główny', 24, 18, 100),

            # Poznań - Zielona Góra
            ('Poznań Główny', 'Zielona Góra', 120, 85, 120),

            # Wrocław - Legnica - Zielona Góra
            ('Wrocław Główny', 'Legnica', 66, 50, 120),
            ('Legnica', 'Zielona Góra', 115, 90, 120),

            # Wrocław - Wałbrzych
            ('Wrocław Główny', 'Świdnica', 53, 45, 100),
            ('Świdnica', 'Wałbrzych Główny', 25, 25, 90),

            # Łódź - Koluszki - Piotrków
            ('Łódź Fabryczna', 'Piotrków Trybunalski', 45, 35, 120),
            ('Piotrków Trybunalski', 'Częstochowa', 60, 45, 120),

            # Gdańsk - Elbląg - Olsztyn
            ('Gdańsk Główny', 'Elbląg', 57, 45, 120),
            ('Elbląg', 'Olsztyn Główny', 92, 70, 120),

            # Białystok - Ełk - Suwałki
            ('Białystok', 'Ełk', 118, 95, 100),
            ('Ełk', 'Suwałki', 58, 50, 100),

            # Lublin - Zamość
            ('Lublin', 'Zamość', 88, 75, 100),

            # Kraków - Rzeszów bezpośrednie
            ('Kraków Główny', 'Rzeszów Główny', 179, 135, 120),

            # Linie regionalne Małopolska
            ('Kraków Główny', 'Oświęcim', 63, 55, 100),
            ('Oświęcim', 'Tychy', 35, 30, 90),

            # Mazowsze - linie aglomeracyjne
            ('Warszawa Centralna', 'Pruszków', 18, 15, 100),

            # Pomorze
            ('Gdańsk Główny', 'Słupsk', 123, 95, 120),
            ('Słupsk', 'Koszalin', 78, 60, 120),
            ('Koszalin', 'Szczecin Główny', 147, 110, 120),

            # Wielkopolska
            ('Poznań Główny', 'Gniezno', 48, 35, 120),
            ('Poznań Główny', 'Kalisz', 110, 80, 120),
            ('Poznań Główny', 'Ostrów Wielkopolski', 89, 65, 120),

            # Dolny Śląsk - Kujawsko-Pomorskie
            ('Wrocław Główny', 'Kalisz', 162, 120, 120),

            # Kujawy
            ('Bydgoszcz Główna', 'Toruń Główny', 45, 30, 120),
            ('Toruń Główny', 'Inowrocław', 38, 30, 100),
            ('Inowrocław', 'Gniezno', 52, 40, 100),

            # Łódzkie - Wielkopolskie
            ('Łódź Fabryczna', 'Kalisz', 115, 85, 120),

            # Mazury
            ('Olsztyn Główny', 'Ełk', 115, 90, 100),

            # Małopolska - Podkarpacie
            ('Tarnów', 'Mielec', 70, 60, 100),
            ('Mielec', 'Rzeszów Główny', 52, 45, 100),

            # Śląsk - Małopolska lokalne
            ('Katowice', 'Oświęcim', 48, 40, 100),

            # Mazowsze lokalne
            ('Warszawa Centralna', 'Płock', 110, 85, 120),

            # Kujawsko-Pomorskie
            ('Bydgoszcz Główna', 'Grudziądz', 58, 45, 100),
        ]

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for from_name, to_name, distance, time, max_speed in connections_data:
            from_station = stations.get(from_name)
            to_station = stations.get(to_name)

            if not from_station:
                self.stdout.write(
                    self.style.ERROR(f'✗ Station not found: {from_name}')
                )
                skipped_count += 1
                continue

            if not to_station:
                self.stdout.write(
                    self.style.ERROR(f'✗ Station not found: {to_name}')
                )
                skipped_count += 1
                continue

            # Twórz połączenie (automatycznie utworzy też połączenie zwrotne)
            connection, created = StationConnection.objects.get_or_create(
                from_station=from_station,
                to_station=to_station,
                defaults={
                    'distance_km': Decimal(str(distance)),
                    'estimated_time_minutes': time,
                    'max_speed_kmh': Decimal(str(max_speed)),
                    'is_bidirectional': True,
                    'active': True,
                }
            )

            if created:
                created_count += 1
                if created_count % 10 == 1:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'🔗 Created: {from_station.name} ↔ {to_station.name} '
                            f'({distance} km, {time} min, max: {max_speed} km/h)'
                        )
                    )
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'\n=== Summary ==='))
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count} connections'))
        self.stdout.write(self.style.WARNING(f'Already existed: {updated_count} connections'))
        self.stdout.write(self.style.ERROR(f'Skipped (missing stations): {skipped_count} connections'))

        # Policz całkowitą liczbę połączeń (w obie strony)
        total_connections = StationConnection.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Total connections in database: {total_connections}'))

        # Statystyki
        self.stdout.write(self.style.SUCCESS(f'\n=== Network Statistics ==='))

        # Najdłuższe połączenia
        longest = StationConnection.objects.order_by('-distance_km')[:5]
        self.stdout.write(self.style.SUCCESS(f'\nLongest connections:'))
        for conn in longest:
            self.stdout.write(f'  {conn.from_station.name} → {conn.to_station.name}: {conn.distance_km} km')

        # Stacje z najwięcej połączeń (huby)
        from django.db.models import Count
        stations_by_connections = Station.objects.annotate(
            connection_count=Count('outgoing_connections')
        ).order_by('-connection_count')[:10]
