from flask import request
from flask_restx import Resource, Namespace, fields
from services.passenger_service import PassengerService
from services.driver_service import DriverService

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
        success = passenger_service.makeRideOffer(current_user.id,_departure_location,_pickup_radius,_destination,
                                                  _drop_radius,_departure_datetime,_notes)
        if success:
            return {"success": True}, 200
        else:
            return {"error": "Failed to make ride offer"}, 500
