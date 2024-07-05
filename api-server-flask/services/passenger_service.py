from models import RideOffers, JoinRideRequests, db, Users

from services.specifications import *
from utils.response import Response
from models.rating_requests import RatingRequest

from geopy.distance import geodesic
from sqlalchemy.exc import IntegrityError


def serializeResult(x):
    result = x[0].to_dict()
    result.update({'ride_status': x[1]})
    return result


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

            if requested_seats < 1:
                raise ValueError("The request must have more than one seat")

            if ride.driver_id == passenger_id:
                raise ValueError("You cannot join the ride you created")

            # Check if the ride has available seats
            if ride.confirmed_passengers + requested_seats > ride.available_seats:
                raise ValueError("No available seats")

            # Create a new join ride request
            join_request = JoinRideRequests(
                ride_id=ride_id,
                passenger_id=passenger_id,
                status='pending',
                requested_seats=requested_seats,
                created_at=datetime.now()
            )
            join_request.save()

            response = Response(success=True, message="Request to join ride successful", status_code=200,
                                data=join_request.to_dict())
            return response.to_tuple()
        except IntegrityError as e:
            response = Response(success=False,
                                message=f"Error joining ride: Cannot send another join request to the same ride",
                                status_code=400)
            return response.to_tuple()

        except Exception as e:
            response = Response(success=False, message=f"Error joining ride: {str(e)}", status_code=400)
            return response.to_tuple()

    def __parse_location(location_str):
        lat, lng = map(float, location_str.split(','))
        return lat, lng

    @staticmethod
    def search_rides(user_id, departure_location=None, pickup_radius=None, destination=None, drop_radius=None,
                     departure_date=None, available_seats=None, delta_hours=5):
        """
        Searches for rides based on location, date, and other criteria.

        Parameters:
        - user_id: int, the ID of the current user
        - departure_location: str, the departure location of the ride
        - pickup_radius: float, the radius from the departure location
        - destination: str, the destination of the ride
        - drop_radius: float, the radius from the destination
        - departure_date: datetime, the datetime of departure
        - available_seats: int, the number of available seats
        - delta_hours: int, the number of hours for the time window (default is 5)

        Returns:
        - response: Response, contains the list of matching rides
        """
        try:
            specifications = list()

            if available_seats:
                specifications.append(AvailableSeatsSpecification(available_seats))
            if departure_date:
                specifications.append(DepartureDateSpecification(departure_date, delta_hours))

            # Add RideStatusSpecification to ensure rides are in "waiting" status
            specifications.append(RideStatusSpecification('waiting'))
            # Add NotMyRideSpecification to ensure rides are not owned by the current user
            specifications.append(NotMyRideSpecification(user_id))

            composite_spec = AndSpecification(*specifications)
            query = Rides.query
            filtered_rides_query = composite_spec.apply(query)
            filtered_rides = filtered_rides_query.all()

            # In-memory filtering for departure and destination locations
            if departure_location and pickup_radius:
                dep_lat, dep_lng = map(float, departure_location.split(','))
                filtered_rides = [
                    ride for ride in filtered_rides
                    if geodesic((dep_lat, dep_lng), parse_location(ride.departure_location)).km <= pickup_radius
                ]

            if destination and drop_radius:
                dest_lat, dest_lng = map(float, destination.split(','))
                filtered_rides = [
                    ride for ride in filtered_rides
                    if geodesic((dest_lat, dest_lng), parse_location(ride.destination)).km <= drop_radius
                ]

            rides_list = [ride.to_dict() for ride in filtered_rides]

            response = Response(success=True, message="Rides retrieved successfully", status_code=200,
                                data={"ride_posts": rides_list})
            return response.to_tuple()
        except Exception as e:
            response = Response(success=False, message=f"Error searching rides: {str(e)}", status_code=400)
            return response.to_tuple()

    @staticmethod
    def get_my_rides(user_id):
        try:
            results = db.session.query(Rides, JoinRideRequests.status).join(JoinRideRequests,
                                                                            Rides.id == JoinRideRequests.ride_id).filter(
                JoinRideRequests.passenger_id == user_id).all()
            return [serializeResult(x) for x in results]
        except Exception as e:
            raise Exception("cannot get the rides", 404)

    @staticmethod
    def rate_ride(user_id,rating_id, rating, comment):
        rating_object = RatingRequest.get_by_id(rating_id)
        if not rating_object:
            return {"success": False,
                    "msg": "This rating does not exist."}, 404
        if rating_object.rating < 0:
            return {"success": False,
                    "msg": "this ride already rated"}, 403
        if rating < 0 or rating > 5:
            return {"success": False,
                    "msg": "the rating must be number from 0 to 5"}, 403
        if not(rating_object.rater_id == user_id):
            return {"success": False,
                    "msg": "cannot rate others ratings"}, 403
        try:
            rating_object.rate(rating,comment)
            response = Response(success=True, message="Rated successfully", status_code=200,)
            return response.to_tuple()
        except Exception as e:
            return {"success": False,
                    "msg": "cannot rate this ride: " + str(e)}, 403


    @staticmethod
    def get_user_rating(user_id):
        user_exists = Users.get_by_id(user_id)
        if not user_exists:
            return {"success": False,
                    "msg": "This user does not exist."}, 404
        try:
            user_rating = RatingRequest.get_average_rating(user_id)
            response = Response(success=True, message="get user rating successfully", status_code=200,
                                data={"rating": user_rating})
            return response.to_tuple()
        except Exception as e:
            return {"success": False,
                    "msg": "cannot get user rating: " + str(e)}, 403

    @staticmethod
    def get_user_comments(user_id):
        user_exists = Users.get_by_id(user_id)
        if not user_exists:
            return {"success": False,
                    "msg": "This user does not exist."}, 404
        try:
            user_comments = RatingRequest.get_comments(user_id)
            response = Response(success=True, message="get user comments successfully", status_code=200,
                                data={"comments": user_comments})
            return response.to_tuple()
        except Exception as e:
            return {"success": False,
                    "msg": "cannot get user comments: " + str(e)}, 403

    @staticmethod
    def get_my_ratings(user_id):
        user_exists = Users.get_by_id(user_id)
        if not user_exists:
            return {"success": False,
                    "msg": "This user does not exist."}, 404
        try:
            my_ratings = RatingRequest.get_pending_ratings(user_id)
            response = Response(success=True, message="get user comments successfully", status_code=200,
                                data={"comments": my_ratings})
            return response.to_tuple()
        except Exception as e:
            return {"success": False,
                    "msg": "cannot get user comments: " + str(e)}, 403



