import pytz
from flask import request
from flask_restx import Resource, Namespace, fields
from services.rating_service import RatingService
from datetime import datetime

from utils.response import Response
from .token_decorators import token_required




rating_service = RatingService()

# Namespace for Driver
authorizations = {'JWT Bearer': {'type': 'apiKey', 'in': 'header', 'name': 'Authorization'}}
ratings_ns = Namespace('rating', description='Rating related operations', authorizations=authorizations)
"""
    Flask-Restx models for api request and response data
"""

ratings_rate_ride = ratings_ns.model('RateRide', {
    "rating_id": fields.Integer(required=True),
    "rating": fields.Integer(required=True),
    "comments": fields.String(required=True),
})

ratings_get_user_rating = ratings_ns.model('GetUserRating', {
    "user_id": fields.Integer(required=True)
})

passenger_remove_rating = ratings_ns.model('RemoveRating',{
    "rating_id": fields.Integer(required=True)
})
ratings_get_ride_ratings = ratings_ns.model('GetRideRatings',{
    "ride_id": fields.Integer(required=True)
})




@ratings_ns.doc(security='JWT Bearer')
@ratings_ns.route('/rating/<int:user_id>/rate-ride')
class RateRide(Resource):

    @ratings_ns.expect(ratings_rate_ride, validate=True)
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
            return RatingService.rate_ride(user_id, rating_id, rating, comments)
        except Exception as e:
            response = Response(success=False,
                                message=f"Error Rate Ride: {str(e)}",
                                status_code=403)
            return response.to_tuple()


@ratings_ns.doc(security='JWT Bearer')
@ratings_ns.route('/rating/get-rating')
class GetUserRating(Resource):

    @ratings_ns.expect(ratings_get_user_rating, validate=True)
    @token_required
    def post(self, current_user):
        req_data = request.get_json()
        user_id = req_data.get("user_id")
        try:
            return RatingService.get_user_rating(user_id)
        except Exception as e:
            response = Response(success=False,
                                message=f"Error Get User Rating: {str(e)}",
                                status_code=403)
            return response.to_tuple()


@ratings_ns.doc(security='JWT Bearer')
@ratings_ns.route('/rating/get-comments')
class GetUserComments(Resource):

    @ratings_ns.expect(ratings_get_user_rating, validate=True)
    @token_required
    def post(self, current_user):
        req_data = request.get_json()
        user_id = req_data.get("user_id")
        try:
            return RatingService.get_user_comments(user_id)
        except Exception as e:
            response = Response(success=False,
                                message=f"Error Get User Rating: {str(e)}",
                                status_code=403)
            return response.to_tuple()


@ratings_ns.doc(security='JWT Bearer')
@ratings_ns.route('/rating/<int:user_id>/my-ratings')
class GetMyRating(Resource):

    @token_required
    def get(self, current_user, user_id):
        if current_user.id != user_id:
            response = Response(success=False,
                                message=f"Error Rate Ride: Unauthorized access to user's Ratings",
                                status_code=403)
            return response.to_tuple()
        try:
            return RatingService.get_my_ratings(user_id)
        except Exception as e:
            response = Response(success=False,
                                message=f"Error Get My Rating: {str(e)}",
                                status_code=403)
            return response.to_tuple()



@ratings_ns.doc(security='JWT Bearer')
@ratings_ns.route('/rating/<int:user_id>/my-ratings-by-ride')
class GetMyRatingByRide(Resource):

    @token_required
    @ratings_ns.expect(ratings_get_ride_ratings, validate=True)
    def post(self, current_user, user_id):
        if current_user.id != user_id:
            response = Response(success=False,
                                message=f"Error Rate Ride By Ride: Unauthorized access to user's Ratings",
                                status_code=403)
            return response.to_tuple()
        try:
            req_data = request.get_json()
            ride_id = req_data.get("ride_id")
            return RatingService.get_my_ratings(user_id,ride_id)
        except Exception as e:
            response = Response(success=False,
                                message=f"Error Get My Rating By Ride: {str(e)}",
                                status_code=403)
            return response.to_tuple()


@ratings_ns.doc(security='JWT Bearer')
@ratings_ns.route('/rating/<int:user_id>/removeRating')
class RemoveRating(Resource):

    @ratings_ns.expect(passenger_remove_rating, validate=True)
    @token_required
    def post(self, current_user, user_id):
        if current_user.id != user_id:
            response = Response(success=False,
                                message=f"Error Remove Rating: Unauthorized access to user's Ratings",
                                status_code=403)
            return response.to_tuple()
        req_data = request.get_json()
        rating_id = req_data.get("rating_id")
        try:
            return RatingService.remove_rating(user_id, rating_id)
        except Exception as e:
            response = Response(success=False,
                                message=f"Error Remove Rating: {str(e)}",
                                status_code=403)
            return response.to_tuple()



