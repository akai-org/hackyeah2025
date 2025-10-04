from django.core.management.base import BaseCommand
from transport.models import Carrier, Vehicle
import random


class Command(BaseCommand):
    help = 'Populate database with Polish railway vehicles (Newag and other manufacturers)'

    def handle(self, *args, **kwargs):
        # Pobierz przewoźników z bazy
        carriers = {
            'PKP IC': Carrier.objects.filter(name='PKP Intercity').first(),
            'SKM': Carrier.objects.filter(name__contains='SKM').first(),
            'KM': Carrier.objects.filter(name='Koleje Mazowieckie').first(),
            'KML': Carrier.objects.filter(name='Koleje Małopolskie').first(),
            'KS': Carrier.objects.filter(name='Koleje Śląskie').first(),
            'KW': Carrier.objects.filter(name='Koleje Wielkopolskie').first(),
            'KD': Carrier.objects.filter(name='Koleje Dolnośląskie').first(),
            'KO': Carrier.objects.filter(name='Koleje Opolskie').first(),
            'PolRegio': Carrier.objects.filter(name='PolRegio').first(),
        }

        # Polskie pojazdy kolejowe
        vehicles_data = [
            # PKP Intercity - Pendolino (ETR610)
            {'carrier': 'PKP IC', 'type': 'TRAIN', 'model': 'ED250 Pendolino', 'id_prefix': 'ED250-', 'count': 20, 'max_speed': 250, 'capacity': 402},
            
            # PKP Intercity - Electric locomotives
            {'carrier': 'PKP IC', 'type': 'TRAIN', 'model': 'EP09', 'id_prefix': 'EP09-', 'count': 15, 'max_speed': 125, 'capacity': 0},
            {'carrier': 'PKP IC', 'type': 'TRAIN', 'model': 'EU07', 'id_prefix': 'EU07-', 'count': 20, 'max_speed': 125, 'capacity': 0},
            
            # PKP Intercity - Wagony
            {'carrier': 'PKP IC', 'type': 'TRAIN', 'model': 'EIP Pendolino (wagon)', 'id_prefix': 'EIP-', 'count': 10, 'max_speed': 200, 'capacity': 380},
            {'carrier': 'PKP IC', 'type': 'TRAIN', 'model': 'IC wagon', 'id_prefix': 'IC-', 'count': 30, 'max_speed': 160, 'capacity': 460},
            
            # NEWAG - Impuls (dla różnych przewoźników)
            {'carrier': 'KM', 'type': 'TRAIN', 'model': 'EN57 (modernizowany)', 'id_prefix': 'EN57-KM-', 'count': 25, 'max_speed': 110, 'capacity': 240},
            {'carrier': 'KM', 'type': 'TRAIN', 'model': 'Newag Impuls 31WE', 'id_prefix': 'EN31WE-', 'count': 8, 'max_speed': 160, 'capacity': 330},
            
            {'carrier': 'KML', 'type': 'TRAIN', 'model': 'Newag Impuls 45WE', 'id_prefix': 'EN45WE-KML-', 'count': 12, 'max_speed': 160, 'capacity': 420},
            {'carrier': 'KML', 'type': 'TRAIN', 'model': 'EN57 (modernizowany)', 'id_prefix': 'EN57-KML-', 'count': 15, 'max_speed': 110, 'capacity': 240},
            
            {'carrier': 'KS', 'type': 'TRAIN', 'model': 'Newag Impuls 31WE', 'id_prefix': 'EN31WE-KS-', 'count': 10, 'max_speed': 160, 'capacity': 330},
            {'carrier': 'KS', 'type': 'TRAIN', 'model': 'Newag Impuls 36WEa', 'id_prefix': 'EN36-KS-', 'count': 8, 'max_speed': 160, 'capacity': 360},
            {'carrier': 'KS', 'type': 'TRAIN', 'model': 'EN57 Śląsk', 'id_prefix': 'EN57-KS-', 'count': 20, 'max_speed': 110, 'capacity': 240},
            
            {'carrier': 'KW', 'type': 'TRAIN', 'model': 'Newag Impuls 31WE', 'id_prefix': 'EN31WE-KW-', 'count': 6, 'max_speed': 160, 'capacity': 330},
            {'carrier': 'KW', 'type': 'TRAIN', 'model': 'EN57 (modernizowany)', 'id_prefix': 'EN57-KW-', 'count': 18, 'max_speed': 110, 'capacity': 240},
            
            {'carrier': 'KD', 'type': 'TRAIN', 'model': 'Newag Impuls 31WE', 'id_prefix': 'EN31WE-KD-', 'count': 7, 'max_speed': 160, 'capacity': 330},
            {'carrier': 'KD', 'type': 'TRAIN', 'model': 'Newag Impuls 45WE', 'id_prefix': 'EN45WE-KD-', 'count': 5, 'max_speed': 160, 'capacity': 420},
            {'carrier': 'KD', 'type': 'TRAIN', 'model': 'PESA Elf', 'id_prefix': 'ELF-KD-', 'count': 8, 'max_speed': 120, 'capacity': 150},
            
            {'carrier': 'KO', 'type': 'TRAIN', 'model': 'Newag Impuls 31WE', 'id_prefix': 'EN31WE-KO-', 'count': 4, 'max_speed': 160, 'capacity': 330},
            {'carrier': 'KO', 'type': 'TRAIN', 'model': 'EN57 (modernizowany)', 'id_prefix': 'EN57-KO-', 'count': 6, 'max_speed': 110, 'capacity': 240},
            
            # SKM - Szybka Kolej Miejska
            {'carrier': 'SKM', 'type': 'TRAIN', 'model': 'EN57 SKM', 'id_prefix': 'EN57-SKM-', 'count': 25, 'max_speed': 110, 'capacity': 240},
            {'carrier': 'SKM', 'type': 'TRAIN', 'model': 'Newag Impuls 31WE SKM', 'id_prefix': 'EN31WE-SKM-', 'count': 8, 'max_speed': 160, 'capacity': 330},
            {'carrier': 'SKM', 'type': 'TRAIN', 'model': 'EN71', 'id_prefix': 'EN71-SKM-', 'count': 10, 'max_speed': 110, 'capacity': 200},
            
            # PolRegio
            {'carrier': 'PolRegio', 'type': 'TRAIN', 'model': 'EN57 PolRegio', 'id_prefix': 'EN57-PR-', 'count': 40, 'max_speed': 110, 'capacity': 240},
            {'carrier': 'PolRegio', 'type': 'TRAIN', 'model': 'SA134', 'id_prefix': 'SA134-PR-', 'count': 20, 'max_speed': 120, 'capacity': 160},
            {'carrier': 'PolRegio', 'type': 'TRAIN', 'model': 'SA132', 'id_prefix': 'SA132-PR-', 'count': 15, 'max_speed': 100, 'capacity': 120},
            
            # PESA - konkurent Newaga
            {'carrier': 'KM', 'type': 'TRAIN', 'model': 'PESA Elf 2', 'id_prefix': 'ELF2-KM-', 'count': 10, 'max_speed': 120, 'capacity': 150},
            {'carrier': 'KML', 'type': 'TRAIN', 'model': 'PESA Elf', 'id_prefix': 'ELF-KML-', 'count': 6, 'max_speed': 120, 'capacity': 150},
            
            # Stadler FLIRT (Szwajcaria, ale używane w Polsce)
            {'carrier': 'KM', 'type': 'TRAIN', 'model': 'Stadler FLIRT', 'id_prefix': 'FLIRT-KM-', 'count': 14, 'max_speed': 160, 'capacity': 300},
            {'carrier': 'KW', 'type': 'TRAIN', 'model': 'Stadler FLIRT', 'id_prefix': 'FLIRT-KW-', 'count': 7, 'max_speed': 160, 'capacity': 300},
        ]

        created_count = 0
        skipped_count = 0
        
        for vehicle_spec in vehicles_data:
            carrier_key = vehicle_spec['carrier']
            carrier = carriers.get(carrier_key)
            
            if not carrier:
                self.stdout.write(
                    self.style.ERROR(f'✗ Carrier {carrier_key} not found in database, skipping vehicles')
                )
                continue
            
            # Generate individual vehicles
            for i in range(1, vehicle_spec['count'] + 1):
                vehicle_id = f"{vehicle_spec['id_prefix']}{i:03d}"
                
                # Calculate average speed (75-85% of max speed)
                avg_speed = round(vehicle_spec['max_speed'] * random.uniform(0.75, 0.85), 2)
                
                vehicle, created = Vehicle.objects.get_or_create(
                    identification_number=vehicle_id,
                    defaults={
                        'carrier': carrier,
                        'type': vehicle_spec['type'],
                        'max_speed': vehicle_spec['max_speed'],
                        'average_speed': avg_speed,
                        'passenger_capacity': vehicle_spec['capacity'],
                        'active': True,
                    }
                )
                
                if created:
                    created_count += 1
                    
                    # Emoji based on speed
                    if vehicle.max_speed >= 200:
                        emoji = '🚄'  # High-speed train
                    elif vehicle.max_speed >= 140:
                        emoji = '🚆'  # Fast train
                    else:
                        emoji = '🚂'  # Regular train
                    
                    # Show progress every 10 vehicles
                    if created_count % 10 == 0 or i == 1:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'{emoji} Created: {vehicle_id} - {vehicle_spec["model"]} '
                                f'({carrier.name}, max: {vehicle.max_speed} km/h, capacity: {vehicle.passenger_capacity})'
                            )
                        )
                else:
                    skipped_count += 1

        self.stdout.write(self.style.SUCCESS(f'\n=== Summary ==='))
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count} vehicles'))
        self.stdout.write(self.style.WARNING(f'Already existed: {skipped_count} vehicles'))
        self.stdout.write(self.style.SUCCESS(f'Total processed: {created_count + skipped_count} vehicles'))
        
        # Statistics by carrier
        self.stdout.write(self.style.SUCCESS(f'\n=== Vehicles by Carrier ==='))
        for carrier_name, carrier in carriers.items():
            if carrier:
                count = Vehicle.objects.filter(carrier=carrier).count()
                self.stdout.write(f'  {carrier.name}: {count} vehicles')
        
        # Statistics by model type
        self.stdout.write(self.style.SUCCESS(f'\n=== Popular Models ==='))
        from django.db.models import Count
        # Group by max_speed ranges
        high_speed = Vehicle.objects.filter(max_speed__gte=200).count()
        fast = Vehicle.objects.filter(max_speed__gte=140, max_speed__lt=200).count()
        regular = Vehicle.objects.filter(max_speed__lt=140).count()
        
        self.stdout.write(f'  🚄 High-speed (≥200 km/h): {high_speed} vehicles')
        self.stdout.write(f'  🚆 Fast trains (140-199 km/h): {fast} vehicles')
        self.stdout.write(f'  🚂 Regular trains (<140 km/h): {regular} vehicles')

