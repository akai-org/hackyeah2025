"""
Helper functions for creating and managing reports
"""
from django.db import transaction
from transport.models import Report, UserReport, Journey, Ticket
from django.utils import timezone


def create_user_report(user, route, from_station, to_station, report_type,
                      delay_minutes=None, description='', image=None,
                      location_latitude=None, location_longitude=None,
                      journey=None, ticket=None, confidence_level=0.5):
    """
    Create a user report with proper validation.

    Args:
        user: User object who is reporting
        route: Route object
        from_station: Starting Station object
        to_station: Ending Station object
        report_type: ReportType object
        delay_minutes: Optional delay in minutes
        description: User's description of the issue
        image: Optional uploaded image
        location_latitude: Optional user's location latitude
        location_longitude: Optional user's location longitude
        journey: Optional specific Journey object
        ticket: Optional Ticket object (for validation)
        confidence_level: How confident user is (0-1)

    Returns:
        tuple: (UserReport, Report, created_new_report, validation_message)
    """

    with transaction.atomic():
        # 1. Walidacja - sprawdź czy użytkownik może zgłaszać
        if not user.is_staff and not ticket:
            # Sprawdź czy użytkownik ma bilet na tę trasę
            valid_tickets = Ticket.objects.filter(
                user=user,
                route=route,
                from_station=from_station,
                to_station=to_station,
                status='VALID'
            )
            if journey:
                valid_tickets = valid_tickets.filter(journey=journey)

            if not valid_tickets.exists():
                return None, None, False, "User needs a valid ticket for this route section"

        # 2. Znajdź lub utwórz zagregowany Report
        report_filters = {
            'route': route,
            'from_station': from_station,
            'to_station': to_station,
            'report_type': report_type,
            'status__in': ['PENDING', 'CONFIRMED']  # Nie dołączaj do zamkniętych raportów
        }

        if journey:
            report_filters['journey'] = journey

        try:
            report = Report.objects.filter(**report_filters).first()

            if not report:
                # Utwórz nowy raport
                report = Report.objects.create(
                    journey=journey,
                    route=route,
                    from_station=from_station,
                    to_station=to_station,
                    report_type=report_type,
                    status='PENDING',
                    user_reports_count=0,
                )
                created_new_report = True
            else:
                created_new_report = False

            # 3. Sprawdź czy użytkownik już zgłaszał ten problem
            existing_user_report = UserReport.objects.filter(
                report=report,
                user=user
            ).first()

            if existing_user_report:
                return existing_user_report, report, False, "User already reported this issue"

            # 4. Utwórz indywidualne zgłoszenie użytkownika
            user_report = UserReport.objects.create(
                report=report,
                user=user,
                ticket=ticket,
                confidence_level=confidence_level,
                delay_minutes=delay_minutes,
                description=description,
                image=image,
                location_latitude=location_latitude,
                location_longitude=location_longitude,
            )

            # UserReport.save() automatycznie wywoła report.recalculate_metrics()

            return user_report, report, created_new_report, "Report created successfully"

        except Exception as e:
            return None, None, False, f"Error creating report: {str(e)}"


def get_user_valid_tickets_for_route(user, route, from_station, to_station, travel_date=None):
    """
    Get user's valid tickets for a specific route section.

    Args:
        user: User object
        route: Route object
        from_station: Starting Station object
        to_station: Ending Station object
        travel_date: Optional date (defaults to today)

    Returns:
        QuerySet of valid Ticket objects
    """
    if travel_date is None:
        travel_date = timezone.now().date()

    return Ticket.objects.filter(
        user=user,
        route=route,
        from_station=from_station,
        to_station=to_station,
        travel_date=travel_date,
        status='VALID'
    )


def get_active_reports_for_journey(journey):
    """
    Get all active reports for a specific journey.

    Args:
        journey: Journey object

    Returns:
        QuerySet of Report objects
    """
    return Report.objects.filter(
        journey=journey,
        status__in=['PENDING', 'CONFIRMED']
    ).select_related(
        'route', 'from_station', 'to_station', 'report_type'
    ).prefetch_related('user_reports__user')


def create_journey_from_route(route, journey_date, vehicle=None):
    """
    Create a Journey instance for a specific date.
    Automatically creates JourneyStatus for each RoutePoint.

    Args:
        route: Route object
        journey_date: Date object
        vehicle: Optional Vehicle object (defaults to route's vehicle)

    Returns:
        Journey object
    """
    if not vehicle:
        vehicle = route.vehicle

    # Calculate departure and arrival times
    first_point = route.route_points.order_by('sequence').first()
    last_point = route.route_points.order_by('-sequence').first()

    if not first_point or not last_point:
        raise ValueError("Route must have at least one route point")

    scheduled_departure = timezone.datetime.combine(
        journey_date,
        first_point.scheduled_departure_time
    )
    scheduled_arrival = timezone.datetime.combine(
        journey_date,
        last_point.scheduled_arrival_time
    )

    journey = Journey.objects.create(
        route=route,
        vehicle=vehicle,
        journey_date=journey_date,
        scheduled_departure=scheduled_departure,
        scheduled_arrival=scheduled_arrival,
        status='SCHEDULED'
    )

    # Journey.save() automatycznie utworzy JourneyStatus dla każdego RoutePoint

    return journey
