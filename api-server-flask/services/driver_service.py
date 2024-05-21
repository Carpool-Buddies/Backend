from models import Rides, JoinRideRequests
from datetime import datetime

from services.future_ride_post import FutureRidePost
from utils.response import Response


class DriverService:

    @staticmethod
    def post_future_ride(_driver_id, _departure_location, _pickup_radius, _destination, _drop_radius,
                         _departure_datetime, _available_seats, _notes):
        """
        Posts a future ride based on provided details.

        Parameters:
        - departure_location: str, the departure location for the ride
        - pickup_radius: float, the pickup radius from the departure location
        - destination: str, the destination of the ride
        - drop_radius: float, the drop radius from the destination
        - departure_datetime: datetime, the date and time of departure
        - available_seats: int, the number of available seats in the ride
        - notes: str (optional), additional notes or preferences for the ride

        Returns:
        - success: bool, indicates whether the ride posting was successful
        """
        try:
            future_ride_post = FutureRidePost(
                driver_id=_driver_id,
                departure_location=_departure_location,
                pickup_radius=_pickup_radius,
                destination=_destination,
                drop_radius=_drop_radius,
                departure_datetime=_departure_datetime,
                available_seats=_available_seats,
                notes=_notes
            )
            future_ride_post.validate()
            future_ride_post.save()

            response = Response(success=True, message="Ride posted successfully", status_code=200,
                                data=future_ride_post.to_response())
            return response.to_tuple()
        except ValueError as ve:
            # Handle validation errors
            response = Response(success=False, message=f"Validation error: {str(ve)}", status_code=400)
            return response.to_tuple()
        except Exception as e:
            # Handle other exceptions, log errors, etc.
            response = Response(success=False, message=f"Error posting future ride: {str(e)}", status_code=500)
            return response.to_tuple()

    @staticmethod
    def get_ride_posts_by_user_id(user_id):
        """
        Fetches ride posts associated with a specific user ID.

        Parameters:
        - user_id: int, the ID of the user whose ride posts to fetch

        Returns:
        - response: tuple, a response object containing success status, message, and ride post data
        """
        try:
            ride_posts = Rides.query.filter_by(driver_id=user_id).all()
            ride_post_dicts = [ride.to_dict() for ride in ride_posts]
            response = Response(success=True, message="Ride posts fetched successfully", status_code=200,
                                data={"ride_posts": ride_post_dicts})
            return response.to_tuple()
        except Exception as e:
            # Handle any exceptions and log the error
            print(f"Error fetching ride posts: {str(e)}")
            response = Response(success=False, message="Error fetching ride posts", status_code=500)
            return response.to_tuple()

    def update_ride_details(ride_id, new_details):
        """
        Updates details for a specific ride post with restrictions.

        Parameters:
        - ride_id: int, the ID of the ride post to be updated
        - new_details: dict, a dictionary containing the updated details for the ride post

        Returns:
        - response: tuple, a response object containing success status and message
        """
        try:
            # Retrieve the ride post by its ID
            ride = Rides.get_by_id(ride_id)

            # Check if the departure_datetime has passed
            if ride.departure_datetime <= datetime.now():
                raise ValueError("Cannot update ride details after the departure time has passed")

            # Prepare new departure datetime for validation
            departure_datetime = new_details.get('departure_datetime', ride.departure_datetime.isoformat())
            if isinstance(departure_datetime, datetime):
                departure_datetime = departure_datetime.isoformat()

            future_ride_post = FutureRidePost(
                driver_id=ride.driver_id,
                departure_location=new_details.get('departure_location', ride.departure_location),
                pickup_radius=new_details.get('pickup_radius', ride.pickup_radius),
                destination=new_details.get('destination', ride.destination),
                drop_radius=new_details.get('drop_radius', ride.drop_radius),
                departure_datetime=departure_datetime,
                available_seats=new_details.get('available_seats', ride.available_seats),
                notes=new_details.get('notes', ride.notes)
            )
            future_ride_post.validate()

            # Update the ride details with the new information
            if not ride.update_details(new_details):
                raise Exception("Error updating ride details")

            response = Response(success=True, message="Ride details updated successfully", status_code=200)
            return response.to_tuple()
        except ValueError as ve:
            # Handle validation errors
            response = Response(success=False, message=f"Validation error: {str(ve)}", status_code=400)
            return response.to_tuple()
        except Exception as e:
            # Handle other exceptions, log errors, etc.
            print(f"Error updating ride details: {str(e)}")
            response = Response(success=False, message="Error updating ride details", status_code=500)
            return response.to_tuple()


    @staticmethod
    def manage_ride_request(ride_id, request_id, status_update):
        """
        Manages passenger ride requests for a specific ride.

        Parameters:
        - ride_id: int, the ID of the ride for which the request is being managed
        - request_id: int, the ID of the ride request being managed
        - status_update: str, the status update ('accept' or 'reject')

        Returns:
        - success: bool, indicates whether the request management was successful
        """
        try:
            # Retrieve the ride
            ride = Rides.query.get_or_404(ride_id)

            # Retrieve the ride request
            ride_request = JoinRideRequests.query.get_or_404(request_id)

            # Handle the status update (accept/reject) for the ride request
            if status_update == 'accept':
                # Update the status of the ride request to accepted
                ride_request.status = 'accepted'

                # Update the number of confirmed passengers for the ride
                ride.confirmed_passengers += 1

                # Notify the passenger about the acceptance
                # TODO: notify_passenger(ride_request.passenger_id, 'accepted')

            elif status_update == 'reject':
                # Update the status of the ride request to rejected
                ride_request.status = 'rejected'

                # Notify the passenger about the rejection
                # TODO: notify_passenger(ride_request.passenger_id, 'rejected')

            # Save changes to the database
            ride.save()
            ride_request.save()

            return True

        except Exception as e:
            print(f"Error managing ride request: {str(e)}")
            return False

    @staticmethod
    def get_pending_join_requests_for_ride(ride_id):
        """
        Retrieves the list of pending join requests for the specified ride.

        Parameters:
        - ride_id: int, the ID of the ride for which to retrieve pending requests

        Returns:
        - list of JoinRideRequests: The list of pending join requests for the ride
        """
        try:
            pending_requests = JoinRideRequests.query.filter_by(ride_id=ride_id, status='pending').all()
            return pending_requests
        except Exception as e:
            print(f"Error retrieving pending requests: {str(e)}")
            return []
