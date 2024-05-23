from flask import request
from flask_restx import Resource, Namespace, fields
from services.passenger_service import PassengerService
from services.driver_service import DriverService
from datetime import datetime
from .token_decorators import token_required

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

passenger_join_ride_request = passenger_ns.model('JoinRideRequest',
                                                 {
                                                     "ride_id": fields.Integer(required=True)
                                                 })

"""
    Flask-Restx routes
"""


@passenger_ns.route('/make-ride-offer')
class PostFutureRides(Resource):
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
@passenger_ns.route('/<int:user_id>/rides')
class GetRides(Resource):
    """
    get the future rides according to date and location
    """
    @token_required
    @passenger_ns.expect(passenger_get_rides, validate=True)
    def put(self,current_user, user_id):
        if current_user.id != user_id:
            return {"message": "Unauthorized access to user's ride posts"}, 403
        req_data = request.get_json()
        date = req_data.get("date")
        resp = passenger_service.get_rides(date)
        return {"ride_posts": resp}, 200


@passenger_ns.doc(security='JWT Bearer')
@passenger_ns.route('/<int:user_id>/rides/join_ride')
class join_ride_request(Resource):
    """
    ask for confirmation to join a ride
    """

    @token_required
    @passenger_ns.expect(passenger_join_ride_request, validate=True)
    def put(self, current_user, user_id):
        try:
            # Check if the current user is authorized to view the ride posts of the specified user
            if current_user.id != user_id:
                return {"message": "Unauthorized access to user's ride posts"}, 403

            req_data = request.get_json()

            # Update ride details using DriverService
            success = passenger_service.join_ride_request(user_id, req_data.get("ride_id"))

            if success:
                return {"success": True}, 200
            else:
                return {"error": "Failed to request to join ride"}, 400

        except Exception as e:
            return {"error": str(e)}, 500
