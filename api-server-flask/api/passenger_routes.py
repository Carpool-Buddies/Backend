import pytz
from flask import request
from flask_restx import Resource, Namespace, fields
from services.passenger_service import PassengerService
from services.driver_service import DriverService
from datetime import datetime

from utils.response import Response
from .token_decorators import token_required

DEFAULT_RADIUS = 10
DEFAULT_AVAILABLE_SEATS = 1

# TODO: After adding the passenger service remove from comment
passenger_service = PassengerService()

# Namespace for Driver
authorizations = {'JWT Bearer': {'type': 'apiKey', 'in': 'header', 'name': 'Authorization'}}
passenger_ns = Namespace('passenger', description='Passenger related operations', authorizations=authorizations)
"""
    Flask-Restx models for api request and response data
"""

passenger_make_ride_offer = passenger_ns.model('PassengerMakeRideOfferModel',
                                               {"departure_location": fields.String(required=True),
                                                "pickup_radius": fields.Float(required=True),
                                                "destination": fields.String(required=True),
                                                "drop_radius": fields.Float(required=True),
                                                "departure_datetime": fields.DateTime(required=True),
                                                "notes": fields.String(required=False)
                                                })

passenger_get_rides = passenger_ns.model('PassengerGetRides', {
    'date': fields.DateTime(required=True)
})

passenger_join_ride_request = passenger_ns.model('JoinRideRequest', {
    "ride_id": fields.Integer(required=True),
    "requested_seats": fields.Integer(required=True)
})

passenger_search_rides = passenger_ns.model('SearchRides', {
    "departure_location": fields.String(required=False),
    "pickup_radius": fields.Float(required=False),
    "destination": fields.String(required=False),
    "drop_radius": fields.Float(required=False),
    "departure_datetime": fields.DateTime(required=False),
    "available_seats": fields.Integer(required=False),
    "delta_hours": fields.Integer(required=False, default=5)
})
passenger_rate_ride = passenger_ns.model('RateRide', {
    "rating_id": fields.Integer(required=True),
    "rating": fields.Integer(required=True),
    "comments": fields.String(required=True),
})

passenger_get_user_rating = passenger_ns.model('GetUserRating', {
    "user_id": fields.Integer(required=True)
})

"""
    Flask-Restx routes
"""


@passenger_ns.doc(security='JWT Bearer')
@passenger_ns.route('/make-ride-offer')
class MakeRideOffer(Resource):
    """
    Allows users to post future rides
    """

    @passenger_ns.expect(passenger_make_ride_offer, validate=True)
    @token_required
    def post(self, current_user):
        req_data = request.get_json()

        # Extract data from the request
        _departure_location = req_data.get("departure_location")
        _pickup_radius = req_data.get("pickup_radius")
        _destination = req_data.get("destination")
        _drop_radius = req_data.get("drop_radius")
        _departure_datetime = req_data.get("departure_datetime")
        _notes = req_data.get("notes")

        # Call the service method to post the future ride
        success = passenger_service.makeRideOffer(current_user.id, _departure_location, _pickup_radius, _destination,
                                                  _drop_radius, _departure_datetime, _notes)
        if success:
            return {"success": True}, 200
        else:
            return {"error": "Failed to make ride offer"}, 500



@passenger_ns.doc(security='JWT Bearer')
@passenger_ns.route('/rides/<int:ride_id>/join-ride')
class JoinRide(Resource):
    """
    Allows passengers to join a ride.
    """

    @passenger_ns.expect(passenger_join_ride_request, validate=True)
    @token_required
    def post(self, current_user, ride_id):
        req_data = request.get_json()
        requested_seats = req_data.get("requested_seats")

        # Check if ride_id in request body matches the ride_id in the URL
        if req_data.get("ride_id") != ride_id:
            response = Response(success=False, message="Ride ID in the request body does not match the URL",
                                status_code=400)
            return response.to_tuple()

        # Join ride using PassengerService
        return PassengerService.join_ride_request(current_user.id, ride_id, requested_seats)


@passenger_ns.doc(security='JWT Bearer')
@passenger_ns.route('/search-rides')
class SearchRides(Resource):
    """
    Allows passengers to search for rides.
    """

    @passenger_ns.expect(passenger_search_rides, validate=True)
    @token_required
    def post(self, current_user):
        req_data = request.get_json()

        departure_location = req_data.get("departure_location", None)
        pickup_radius = req_data.get("pickup_radius", DEFAULT_RADIUS)
        destination = req_data.get("destination", None)
        drop_radius = req_data.get("drop_radius", DEFAULT_RADIUS)
        departure_date_str = req_data.get("departure_datetime", None)
        available_seats = req_data.get("available_seats", DEFAULT_AVAILABLE_SEATS)
        delta_hours = req_data.get("delta_hours", 5)

        # Parse departure_date as datetime
        if departure_date_str:
            # departure_date = datetime.fromisoformat(departure_date_str)
            departure_date = datetime.strptime(departure_date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            departure_date = datetime.now()

        # Search rides using PassengerService
        return PassengerService.search_rides(current_user.id, departure_location, pickup_radius, destination,
                                             drop_radius,
                                             departure_date, available_seats, delta_hours)


@passenger_ns.doc(security='JWT Bearer')
@passenger_ns.route('/<int:user_id>/rides')
class GetMyRideRequests(Resource):
    @token_required
    def get(self, current_user, user_id):
        if current_user.id != user_id:
            response = Response(success=False,
                                message=f"Error Get My Ride Requests: Unauthorized access to user's ride requests",
                                status_code=403)
            return response.to_tuple()
        try:
            resp = passenger_service.get_my_rides(user_id)
        except Exception as e:
            response = Response(success=False,
                                message=f"Error Get My Ride Requests: {str(e.args[0])}",
                                status_code=403)
            return response.to_tuple()
        response = Response(success=True,
                            message=f"success in get requests",
                            status_code=200,
                            data={"data":resp})
        return response.to_tuple()


@passenger_ns.doc(security='JWT Bearer')
@passenger_ns.route('/rating/<int:user_id>/rate-ride')
class RateRide(Resource):


    @passenger_ns.expect(passenger_rate_ride, validate=True)
    @token_required
    def post(self, current_user, user_id):
        if current_user.id != user_id:
            response = Response(success=False,
                                message=f"Error Rate Ride: Unauthorized access to user's Ratings",
                                status_code=403)
            return response.to_tuple()
        req_data = request.get_json()
        rating_id = req_data.get("rating_id")
        rating = req_data.get("rating")
        comments = req_data.get("comments")
        try:
            return PassengerService.rate_ride(rating_id, rating, comments)
        except Exception as e:
            response = Response(success=False,
                                message=f"Error Rate Ride: {str(e)}",
                                status_code=403)
            return response.to_tuple()



@passenger_ns.doc(security='JWT Bearer')
@passenger_ns.route('/rating/get-rating')
class GetUserRating(Resource):


    @passenger_ns.expect(passenger_get_user_rating, validate=True)
    @token_required
    def post(self, current_user):
        req_data = request.get_json()
        user_id = req_data.get("user_id")
        try:
            return PassengerService.get_user_rating(user_id)
        except Exception as e:
            response = Response(success=False,
                                message=f"Error Get User Rating: {str(e)}",
                                status_code=403)
            return response.to_tuple()

@passenger_ns.doc(security='JWT Bearer')
@passenger_ns.route('/rating/get-comments')
class GetUserComments(Resource):

    @passenger_ns.expect(passenger_get_user_rating, validate=True)
    @token_required
    def post(self, current_user):
        req_data = request.get_json()
        user_id = req_data.get("user_id")
        try:
            return PassengerService.get_user_comments(user_id)
        except Exception as e:
            response = Response(success=False,
                                message=f"Error Get User Rating: {str(e)}",
                                status_code=403)
            return response.to_tuple()


@passenger_ns.doc(security='JWT Bearer')
@passenger_ns.route('/rating/<int:user_id>/my-ratings')
class GetMyRating(Resource):

    @token_required
    def Get(self, current_user,user_id):
        if current_user.id != user_id:
            response = Response(success=False,
                                message=f"Error Rate Ride: Unauthorized access to user's Ratings",
                                status_code=403)
            return response.to_tuple()
        try:
            return PassengerService.get_my_ratings(user_id)
        except Exception as e:
            response = Response(success=False,
                                message=f"Error Get My Rating: {str(e)}",
                                status_code=403)
            return response.to_tuple()
