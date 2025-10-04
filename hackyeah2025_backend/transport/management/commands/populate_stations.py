from django.core.management.base import BaseCommand
from transport.models import Station, StationType


class Command(BaseCommand):
    help = 'Populate database with 50 Polish railway stations'

    def handle(self, *args, **kwargs):
        # Create or get station type
        station_type, created = StationType.objects.get_or_create(
            id=1,
            defaults={'name': 'Dworzec kolejowy'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created station type: {station_type.name}'))

        # 50 Polish cities with their railway stations and coordinates
        polish_stations = [
            {'name': 'Warszawa Centralna', 'location': 'Warszawa, ul. Aleje Jerozolimskie 54', 'lat': 52.2297, 'lon': 21.0122, 'capacity': 20},
            {'name': 'Kraków Główny', 'location': 'Kraków, ul. Pawia 5a', 'lat': 50.0677, 'lon': 19.9476, 'capacity': 15},
            {'name': 'Wrocław Główny', 'location': 'Wrocław, ul. Piłsudskiego 105', 'lat': 51.0989, 'lon': 17.0366, 'capacity': 15},
            {'name': 'Poznań Główny', 'location': 'Poznań, ul. Dworcowa 1', 'lat': 52.4015, 'lon': 16.9074, 'capacity': 12},
            {'name': 'Gdańsk Główny', 'location': 'Gdańsk, ul. Podwale Grodzkie 1', 'lat': 54.3561, 'lon': 18.6442, 'capacity': 12},
            {'name': 'Łódź Fabryczna', 'location': 'Łódź, ul. Fabryczna 1', 'lat': 51.7681, 'lon': 19.4565, 'capacity': 10},
            {'name': 'Katowice', 'location': 'Katowice, ul. Dworcowa 1', 'lat': 50.2575, 'lon': 19.0180, 'capacity': 12},
            {'name': 'Szczecin Główny', 'location': 'Szczecin, ul. Kolumba 1', 'lat': 53.4285, 'lon': 14.5528, 'capacity': 10},
            {'name': 'Bydgoszcz Główna', 'location': 'Bydgoszcz, ul. Dworcowa 77', 'lat': 53.1332, 'lon': 18.0090, 'capacity': 10},
            {'name': 'Lublin', 'location': 'Lublin, pl. Dworcowy 1', 'lat': 51.2465, 'lon': 22.5684, 'capacity': 8},
            {'name': 'Białystok', 'location': 'Białystok, ul. Kolejowa 11', 'lat': 53.1325, 'lon': 23.1688, 'capacity': 8},
            {'name': 'Gdynia Główna', 'location': 'Gdynia, pl. Konstytucji 1', 'lat': 54.5189, 'lon': 18.5402, 'capacity': 10},
            {'name': 'Częstochowa', 'location': 'Częstochowa, al. Wolności 27', 'lat': 50.8118, 'lon': 19.1203, 'capacity': 8},
            {'name': 'Radom', 'location': 'Radom, ul. Kilińskiego 16', 'lat': 51.4027, 'lon': 21.1471, 'capacity': 6},
            {'name': 'Toruń Główny', 'location': 'Toruń, ul. Kujawska 1', 'lat': 53.0138, 'lon': 18.6048, 'capacity': 8},
            {'name': 'Kielce', 'location': 'Kielce, pl. Dworcowy 2', 'lat': 50.8661, 'lon': 20.6286, 'capacity': 6},
            {'name': 'Gliwice', 'location': 'Gliwice, ul. Dworcowa 23', 'lat': 50.2945, 'lon': 18.6714, 'capacity': 8},
            {'name': 'Zabrze', 'location': 'Zabrze, ul. Dworcowa 1', 'lat': 50.3249, 'lon': 18.7856, 'capacity': 6},
            {'name': 'Olsztyn Główny', 'location': 'Olsztyn, pl. Jedności Słowiańskiej 1', 'lat': 53.7784, 'lon': 20.4801, 'capacity': 8},
            {'name': 'Rzeszów Główny', 'location': 'Rzeszów, pl. Dworcowy 1', 'lat': 50.0362, 'lon': 22.0055, 'capacity': 8},
            {'name': 'Opole Główne', 'location': 'Opole, ul. Krakowska 55', 'lat': 50.6751, 'lon': 17.9213, 'capacity': 6},
            {'name': 'Zielona Góra', 'location': 'Zielona Góra, ul. Dworcowa 1', 'lat': 51.9356, 'lon': 15.5062, 'capacity': 6},
            {'name': 'Elbląg', 'location': 'Elbląg, ul. Dworcowa 1', 'lat': 54.1522, 'lon': 19.4085, 'capacity': 6},
            {'name': 'Płock', 'location': 'Płock, ul. Bielska 1', 'lat': 52.5460, 'lon': 19.7065, 'capacity': 5},
            {'name': 'Wałbrzych Główny', 'location': 'Wałbrzych, ul. 1 Maja 154', 'lat': 50.7844, 'lon': 16.2844, 'capacity': 6},
            {'name': 'Tarnów', 'location': 'Tarnów, pl. Dworcowy 1', 'lat': 50.0134, 'lon': 20.9886, 'capacity': 6},
            {'name': 'Koszalin', 'location': 'Koszalin, ul. Dworcowa 1', 'lat': 54.1942, 'lon': 16.1714, 'capacity': 6},
            {'name': 'Kalisz', 'location': 'Kalisz, ul. Dworcowa 2', 'lat': 51.7607, 'lon': 18.0814, 'capacity': 5},
            {'name': 'Grudziądz', 'location': 'Grudziądz, ul. Dworcowa 1', 'lat': 53.4836, 'lon': 18.7537, 'capacity': 5},
            {'name': 'Słupsk', 'location': 'Słupsk, ul. Szczecińska 26', 'lat': 54.4641, 'lon': 17.0283, 'capacity': 6},
            {'name': 'Legnica', 'location': 'Legnica, ul. Dworcowa 1', 'lat': 51.2070, 'lon': 16.1619, 'capacity': 5},
            {'name': 'Tychy', 'location': 'Tychy, ul. Dworcowa 1', 'lat': 50.1352, 'lon': 18.9653, 'capacity': 5},
            {'name': 'Jaworzno Szczakowa', 'location': 'Jaworzno, ul. Grunwaldzka 272', 'lat': 50.1952, 'lon': 19.2767, 'capacity': 6},
            {'name': 'Ełk', 'location': 'Ełk, ul. Dworcowa 1', 'lat': 53.8276, 'lon': 22.3617, 'capacity': 5},
            {'name': 'Siedlce', 'location': 'Siedlce, ul. Piłsudskiego 56', 'lat': 52.1676, 'lon': 22.2901, 'capacity': 5},
            {'name': 'Zamość', 'location': 'Zamość, ul. Szczebrzeska 11', 'lat': 50.7231, 'lon': 23.2519, 'capacity': 5},
            {'name': 'Pruszków', 'location': 'Pruszków, ul. Dworcowa 1', 'lat': 52.1705, 'lon': 20.8117, 'capacity': 6},
            {'name': 'Mielec', 'location': 'Mielec, ul. Dworcowa 1', 'lat': 50.2874, 'lon': 21.4238, 'capacity': 5},
            {'name': 'Konin', 'location': 'Konin, ul. Dworcowa 1', 'lat': 52.2232, 'lon': 18.2518, 'capacity': 5},
            {'name': 'Inowrocław', 'location': 'Inowrocław, ul. Dworcowa 1', 'lat': 52.7978, 'lon': 18.2597, 'capacity': 5},
            {'name': 'Sopot', 'location': 'Sopot, ul. Dworcowa 1', 'lat': 54.4421, 'lon': 18.5602, 'capacity': 6},
            {'name': 'Piła Główna', 'location': 'Piła, ul. Dworcowa 76', 'lat': 53.1508, 'lon': 16.7380, 'capacity': 5},
            {'name': 'Ostrów Wielkopolski', 'location': 'Ostrów Wielkopolski, ul. Dworcowa 1', 'lat': 51.6514, 'lon': 17.8106, 'capacity': 5},
            {'name': 'Stargard', 'location': 'Stargard, ul. Dworcowa 1', 'lat': 53.3368, 'lon': 15.0503, 'capacity': 5},
            {'name': 'Gniezno', 'location': 'Gniezno, ul. Dworcowa 1', 'lat': 52.5348, 'lon': 17.5825, 'capacity': 5},
            {'name': 'Świdnica', 'location': 'Świdnica, ul. Dworcowa 1', 'lat': 50.8460, 'lon': 16.4897, 'capacity': 5},
            {'name': 'Piotrków Trybunalski', 'location': 'Piotrków Trybunalski, ul. Dworcowa 1', 'lat': 51.4055, 'lon': 19.7031, 'capacity': 5},
            {'name': 'Suwałki', 'location': 'Suwałki, ul. Dworcowa 1', 'lat': 54.1116, 'lon': 22.9308, 'capacity': 5},
            {'name': 'Oświęcim', 'location': 'Oświęcim, ul. Dworcowa 1', 'lat': 50.0347, 'lon': 19.2390, 'capacity': 5},
            {'name': 'Nowy Sącz', 'location': 'Nowy Sącz, ul. Kilińskiego 1', 'lat': 49.6248, 'lon': 20.7149, 'capacity': 5},
            {'name': 'Rabka-Zdrój', 'location': 'Rabka-Zdrój, ul. Parkowa 1', 'lat': 49.6108, 'lon': 19.9653, 'capacity': 4},
            {'name': 'Sucha Beskidzka', 'location': 'Sucha Beskidzka, ul. Dworcowa 1', 'lat': 49.7411, 'lon': 19.5967, 'capacity': 4},
        ]

        created_count = 0
        updated_count = 0

        for station_data in polish_stations:
            station, created = Station.objects.get_or_create(
                name=station_data['name'],
                defaults={
                    'location': station_data['location'],
                    'latitude': station_data['lat'],
                    'longitude': station_data['lon'],
                    'type': station_type,
                    'platform_capacity': station_data['capacity'],
                    'current_occupancy': 0,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {station.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'○ Already exists: {station.name}'))

        self.stdout.write(self.style.SUCCESS(f'\n=== Summary ==='))
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count} stations'))
        self.stdout.write(self.style.WARNING(f'Already existed: {updated_count} stations'))
        self.stdout.write(self.style.SUCCESS(f'Total: {created_count + updated_count} stations'))
