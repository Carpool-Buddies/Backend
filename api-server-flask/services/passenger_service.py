import pytz
from sqlalchemy import or_

from models import RideOffers, Rides, JoinRideRequests
from datetime import datetime,timedelta


class PassengerService:
    @staticmethod
    def makeRideOffer(_passenger_id, _departure_location, _pickup_radius, _destination, _drop_radius,
                      _departure_datetime, _notes):
        """
        make Ride Offer based on provided details.

        Parameters:
        - departure_location: str, the departure location for the ride
        - pickup_radius: float, the pickup radius from the departure location
        - destination: str, the destination of the ride
        - drop_radius: float, the drop radius from the destination
        - departure_datetime: datetime, the date and time of departure
        - notes: str (optional), additional notes or preferences for the ride

        Returns:
        - success: bool, indicates whether the ride posting was successful
        """
        try:
            # Ensure departure_datetime is in the future
            if _departure_datetime <= datetime.now():
                raise ValueError("Departure date must be in the future")

            # Create a new Ride object with the provided details
            new_ride = RideOffers(passenger_id=_passenger_id,
                             departure_location=_departure_location,
                             pickup_radius=_pickup_radius,
                             destination=_destination,
                             drop_radius=_drop_radius,
                             departure_datetime=_departure_datetime,
                             notes=_notes
                             )
            # Save the new ride to the database
            new_ride.save()

            # Return success indicating the ride was posted successfully
            return True
        except ValueError as ve:
            # Handle validation errors
            print(f"Validation error: {str(ve)}")
            return False
        except Exception as e:
            # Handle other exceptions, log errors, etc.
            print(f"Error making ride offer: {str(e)}")
            return False

    @staticmethod
    def join_ride_request(passenger_id,ride_id):
        ride = Rides.get_by_id(ride_id)
        if ride.available_seats > 0:
            join_request = JoinRideRequests(passenger_id = passenger_id,ride_id= ride_id)
            join_request.save()
            return True
        return False

    @staticmethod
    def get_rides(date):
        date.replace(tzinfo=None)
        window_start = date - timedelta(minutes=30)
        window_end = date + timedelta(minutes=30)
        now = datetime.now()
        return Rides.query.filter(
            Rides.departure_datetime > now,
            Rides.departure_datetime.between(window_start, window_end),
            Rides.available_seats > 1,
            Rides.status == 'waiting'
        ).all()
