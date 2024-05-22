from models import RideOffers, JoinRideRequests
import pytz
from services.specifications import *
from utils.response import Response
from datetime import datetime, timedelta

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

    @staticmethod
    def join_ride_request(passenger_id, ride_id, requested_seats):
        """
        Allows a passenger to join a ride.

        Parameters:
        - passenger_id: int, the ID of the passenger requesting to join the ride
        - ride_id: int, the ID of the ride to join
        - requested_seats: int, the number of seats requested by the passenger

        Returns:
        - response: Response, contains success status and message
        """
        try:
            # Retrieve the ride
            ride = Rides.query.get_or_404(ride_id)

            # Check if the ride has available seats
            if ride.confirmed_passengers + requested_seats > ride.available_seats:
                raise ValueError("No available seats")

            # Create a new join ride request
            join_request = JoinRideRequests(
                ride_id=ride_id,
                passenger_id=passenger_id,
                status='pending',
                requested_seats=requested_seats
            )
            join_request.save()

            response = Response(success=True, message="Request to join ride successful", status_code=200)
            return response.to_tuple()
        except Exception as e:
            response = Response(success=False, message=f"Error joining ride: {str(e)}", status_code=400)
            return response.to_tuple()

    @staticmethod
    def search_rides(departure_location=None, pickup_radius=None, destination=None, drop_radius=None,
                     departure_date=None, available_seats=1):
        """
        Searches for rides based on location, date, and other criteria.

        Parameters:
        - departure_location: str, the departure location of the ride
        - pickup_radius: float, the radius from the departure location
        - destination: str, the destination of the ride
        - drop_radius: float, the radius from the destination
        - departure_date: date, the date of departure
        - available_seats: int, the number of available seats

        Returns:
        - response: Response, contains the list of matching rides
        """
        try:
            specifications = []

            if departure_location and pickup_radius:
                specifications.append(DepartureLocationSpecification(departure_location, pickup_radius))
            if destination and drop_radius:
                specifications.append(DestinationLocationSpecification(destination, drop_radius))
            if available_seats:
                specifications.append(AvailableSeatsSpecification(available_seats))
            if departure_date is None:
                # Set departure_date to current time in Israel if not provided
                israel_tz = pytz.timezone('Asia/Jerusalem')
                departure_date = datetime.now(israel_tz)

            specifications.append(DepartureDateSpecification(departure_date))

            composite_spec = AndSpecification(*specifications)
            query = Rides.query
            filtered_rides = composite_spec.apply(query)

            rides_list = [ride.to_dict() for ride in filtered_rides]

            response = Response(success=True, message="Rides retrieved successfully", status_code=200, data=rides_list)
            return response.to_tuple()
        except Exception as e:
            response = Response(success=False, message=f"Error searching rides: {str(e)}", status_code=400)
            return response.to_tuple()