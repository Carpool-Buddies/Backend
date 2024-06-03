from datetime import datetime, timedelta

from models import Rides


class FutureRidePost:
    def __init__(self, driver_id, departure_location, pickup_radius, destination, drop_radius, departure_datetime,
                 available_seats, notes):
        self.driver_id = driver_id
        self.departure_location = departure_location
        self.pickup_radius = pickup_radius
        self.destination = destination
        self.drop_radius = drop_radius
        self.departure_datetime = departure_datetime
        self.available_seats = available_seats
        self.notes = notes

    def validate(self):
        try:
            self.departure_datetime = datetime.strptime(self.departure_datetime, '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            raise ValueError("Invalid date format. Use ISO 8601 format: 'YYYY-MM-DDTHH:MM:SS.sssZ'.")

        if self.departure_datetime <= datetime.now():
            raise ValueError("Departure date must be in the future")

        if self.available_seats <= 0:
            raise ValueError("Available seats must be greater than 0")

        if self.has_ride_within_next_five_hours():
            raise ValueError("Driver already has a ride scheduled within the next 5 hours")

    def has_ride_within_next_five_hours(self):
        now = datetime.now()
        five_hours_before = self.departure_datetime - timedelta(hours=5)
        five_hours_after = self.departure_datetime + timedelta(hours=5)

        # Check if the driver has rides within the next five hours
        existing_rides = Rides.query.filter(
            Rides.driver_id == self.driver_id,
            Rides.departure_datetime.between(max(five_hours_before, now), five_hours_after)
        ).all()

        if len(existing_rides) > 0:
            return True

        # Check if the driver's last ride within the five hours before self.departure_datetime is completed
        last_ride = Rides.query.filter(
            Rides.driver_id == self.driver_id,
            Rides.departure_datetime < self.departure_datetime,
            Rides.departure_datetime >= five_hours_before
        ).order_by(Rides.departure_datetime.desc()).first()

        if last_ride and last_ride.ride_status != 'Completed':
            return True

        return False

    def save(self):
        new_ride = Rides(
            driver_id=self.driver_id,
            departure_location=self.departure_location,
            pickup_radius=self.pickup_radius,
            destination=self.destination,
            drop_radius=self.drop_radius,
            departure_datetime=self.departure_datetime,
            available_seats=self.available_seats,
            notes=self.notes
        )
        new_ride.save()
        return new_ride

    def to_response(self):
        return {
            "driver_id": self.driver_id,
            "departure_location": self.departure_location,
            "pickup_radius": self.pickup_radius,
            "destination": self.destination,
            "drop_radius": self.drop_radius,
            "departure_datetime": self.departure_datetime.isoformat(),
            "available_seats": self.available_seats,
            "notes": self.notes
        }
