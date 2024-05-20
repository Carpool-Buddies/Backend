from flask import request
from flask_restx import Resource, Namespace, fields

from services.driver_service import DriverService

from .token_decorators import token_required

driver_service = DriverService()

# Namespace for Driver
authorizations = {'JWT Bearer': {'type': 'apiKey', 'in': 'header', 'name': 'Authorization'}}
driver_ns = Namespace('driver', description='Driver related operations', authorizations=authorizations)
"""
    Flask-Restx models for api request and response data
"""

driver_post_future_ride_model = driver_ns.model('DriverPostFutureRideModel', {"departure_location": fields.String(required=True),
                                                                            "pickup_radius": fields.Float(required=True),
                                                                            "destination": fields.String(required=True),
                                                                            "drop_radius": fields.Float(required=True),
                                                                            "departure_datetime": fields.DateTime(required=True),
                                                                            "available_seats": fields.Integer(required=True),
                                                                            "notes": fields.String(required=False)
                                                                            })

update_ride_model = driver_ns.model('UpdateRideModel', {"departure_location": fields.String(required=True),
                                                        "pickup_radius": fields.Float(required=True),
                                                        "destination": fields.String(required=True),
                                                        "drop_radius": fields.Float(required=True),
                                                        "departure_datetime": fields.DateTime(required=True),
                                                        "available_seats": fields.Integer(required=True),
                                                        "notes": fields.String()
                                                        })


ride_request_model = driver_ns.model('RideRequestModel', {'passenger_id': fields.Integer(required=True),
                                                        'status': fields.String(required=True)
                                                        })


"""
    Flask-Restx routes
"""

@driver_ns.doc(security='JWT Bearer')
@driver_ns.route('/post-future-rides')
class PostFutureRides(Resource):
    """
    Allows users to post future rides
    """

    @driver_ns.expect(driver_post_future_ride_model, validate=True)
    @token_required
    def post(self, current_user):
        req_data = request.get_json()

        # Extract data from the request
        _departure_location = req_data.get("departure_location")
        _pickup_radius = req_data.get("pickup_radius")
        _destination = req_data.get("destination")
        _drop_radius = req_data.get("drop_radius")
        _departure_datetime = req_data.get("departure_datetime")
        _available_seats = req_data.get("available_seats")
        _notes = req_data.get("notes")

        # Call the service method to post the future ride
        return driver_service.post_future_ride(current_user.id, _departure_location, _pickup_radius, _destination,
                                                  _drop_radius, _departure_datetime, _available_seats, _notes)


@driver_ns.doc(security='JWT Bearer')
@driver_ns.route('/<int:user_id>/rides')
class ManageUserRidePosts(Resource):
    """
    Allows users to manage their ride posts
    """

    @token_required
    def get(self, current_user, user_id):
        # Check if the current user is authorized to view the ride posts of the specified user
        if current_user.id != user_id:
            return {"message": "Unauthorized access to user's ride posts"}, 403

        # Fetch the ride posts associated with the specified user ID using DriverService
        ride_posts = DriverService.get_ride_posts_by_user_id(user_id)

        return {"ride_posts": ride_posts}, 200

@driver_ns.doc(security='JWT Bearer')
@driver_ns.route('/<int:user_id>/rides/<int:ride_id>/update')
class UpdateRideDetails(Resource):
    """
    Edits ride details using 'update_ride_model' input
    """

    @driver_ns.expect(update_ride_model)
    @token_required
    def put(self, current_user, user_id, ride_id):
        try:
            # Check if the current user is authorized to view the ride posts of the specified user
            if current_user.id != user_id:
                return {"message": "Unauthorized access to user's ride posts"}, 403

            req_data = request.get_json()

            # Update ride details using DriverService
            success = DriverService.update_ride_details(ride_id, req_data)

            if success:
                return {"success": True}, 200
            else:
                return {"error": "Failed to update ride details"}, 400

        except Exception as e:
            return {"error": str(e)}, 500


@driver_ns.doc(security='JWT Bearer')
@driver_ns.route('/<int:user_id>/rides/manage_requests/<int:ride_id>')
class ManagePassengerRequests(Resource):
    """
    Allows users to manage passenger join ride requests for a specific future ride post.
    """

    @token_required
    def get(self, current_user, user_id, ride_id):
        """
        Retrieves the list of pending join requests for the selected ride.
        """
        try:
            # Check if the current user is authorized to view the ride posts of the specified user
            if current_user.id != user_id:
                return {"message": "Unauthorized access to user's ride posts"}, 403

            # Retrieve pending join requests using the service
            pending_requests = DriverService.get_pending_join_requests_for_ride(ride_id)

            # Format the pending requests data
            pending_requests_data = [request.to_dict() for request in pending_requests]

            return {"pending_requests": pending_requests_data}, 200

        except Exception as e:
            return {"error": str(e)}, 500

    @driver_ns.expect(ride_request_model)
    @token_required
    def put(self, current_user, user_id, ride_id):
        """
        Manages passenger join ride requests for the selected ride.
        """
        try:
            # Check if the current user is authorized to view the ride posts of the specified user
            if current_user.id != user_id:
                return {"message": "Unauthorized access to user's ride posts"}, 403

            req_data = request.get_json()

            # Extract request ID and status update from request data
            request_id = req_data.get("request_id")
            status_update = req_data.get("status_update")

            # Manage ride request using DriverService
            success = DriverService.manage_ride_request(ride_id, request_id, status_update)

            if success:
                return {"success": True}, 200
            else:
                return {"error": "Failed to manage ride request"}, 400

        except Exception as e:
            return {"error": str(e)}, 500