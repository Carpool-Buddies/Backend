from models import RideOffers
from datetime import datetime


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
            print(f"Error posting future ride: {str(e)}")
            return False
