from django.core.management.base import BaseCommand
from transport.models import Carrier


class Command(BaseCommand):
    help = 'Populate database with Polish railway carriers'

    def handle(self, *args, **kwargs):
        # Polscy przewoźnicy kolejowi z priorytetami
        polish_carriers = [
            {
                'name': 'PKP Intercity',
                'priority': 10,
                'ticket_purchase_link': 'https://www.intercity.pl',
            },
            {
                'name': 'PKP SKM (Szybka Kolej Miejska)',
                'priority': 8,
                'ticket_purchase_link': 'https://www.skm.pkp.pl',
            },
            {
                'name': 'Koleje Małopolskie',
                'priority': 7,
                'ticket_purchase_link': 'https://www.malopolskiekoleje.pl',
            },
            {
                'name': 'Koleje Mazowieckie',
                'priority': 7,
                'ticket_purchase_link': 'https://www.mazowieckie.com.pl',
            },
            {
                'name': 'Koleje Śląskie',
                'priority': 7,
                'ticket_purchase_link': 'https://www.kolejeslaskie.com',
            },
            {
                'name': 'Koleje Wielkopolskie',
                'priority': 7,
                'ticket_purchase_link': 'https://www.kolejewlkp.pl',
            },
            {
                'name': 'Koleje Dolnośląskie',
                'priority': 7,
                'ticket_purchase_link': 'https://www.kolejedolnoslaskie.eu',
            },
            {
                'name': 'PolRegio',
                'priority': 6,
                'ticket_purchase_link': 'https://polregio.pl',
            },
            {
                'name': 'Leo Express',
                'priority': 6,
                'ticket_purchase_link': 'https://www.leoexpress.com/pl',
            },
            {
                'name': 'RegioJet',
                'priority': 6,
                'ticket_purchase_link': 'https://www.regiojet.pl',
            },
            {
                'name': 'Arriva RP',
                'priority': 5,
                'ticket_purchase_link': 'https://www.arriva.pl',
            },
            {
                'name': 'Koleje Kujawsko-Pomorskie',
                'priority': 6,
                'ticket_purchase_link': 'https://www.kk-p.pl',
            },
            {
                'name': 'Łódzka Kolej Aglomeracyjna',
                'priority': 6,
                'ticket_purchase_link': 'https://lka.lodzkie.pl',
            },
            {
                'name': 'Szybka Kolej Miejska w Trójmieście',
                'priority': 7,
                'ticket_purchase_link': 'https://www.skm.pkp.pl',
            },
            {
                'name': 'Koleje Opolskie',
                'priority': 6,
                'ticket_purchase_link': 'https://www.koleje-opolskie.com.pl',
            },
            {
                'name': 'Przewozy Regionalne',
                'priority': 6,
                'ticket_purchase_link': 'https://www.przewozyregionalne.pl',
            },
        ]

        created_count = 0
        updated_count = 0

        for carrier_data in polish_carriers:
            carrier, created = Carrier.objects.get_or_create(
                name=carrier_data['name'],
                defaults={
                    'priority': carrier_data['priority'],
                    'ticket_purchase_link': carrier_data['ticket_purchase_link'],
                }
            )
            
            if created:
                created_count += 1
                # Emoji based on priority
                if carrier.priority >= 8:
                    emoji = '⭐'
                elif carrier.priority >= 6:
                    emoji = '🚂'
                else:
                    emoji = '🚆'
                    
                self.stdout.write(
                    self.style.SUCCESS(f'{emoji} Created: {carrier.name} (priority: {carrier.priority})')
                )
            else:
                # Update if exists
                carrier.priority = carrier_data['priority']
                carrier.ticket_purchase_link = carrier_data['ticket_purchase_link']
                carrier.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'○ Updated: {carrier.name} (priority: {carrier.priority})')
                )

        self.stdout.write(self.style.SUCCESS(f'\n=== Summary ==='))
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count} carriers'))
        self.stdout.write(self.style.WARNING(f'Updated: {updated_count} carriers'))
        self.stdout.write(self.style.SUCCESS(f'Total: {created_count + updated_count} carriers'))
        
        # Display carriers by priority
        self.stdout.write(self.style.SUCCESS(f'\n=== Carriers by Priority ==='))
        carriers_by_priority = Carrier.objects.all().order_by('-priority', 'name')
        for carrier in carriers_by_priority:
            self.stdout.write(f'  [{carrier.priority}] {carrier.name}')

