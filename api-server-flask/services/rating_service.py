from models import RideOffers, JoinRideRequests, db, Users

from services.specifications import *
from utils.response import Response
from models.rating_requests import RatingRequest

from geopy.distance import geodesic
from sqlalchemy.exc import IntegrityError


class RatingService:

    @staticmethod
    def rate_ride(user_id, rating_id, rating, comment):
        rating_object = RatingRequest.get_by_id(rating_id)
        if not rating_object:
            return {"success": False,
                    "msg": "This rating does not exist."}, 404
        if rating_object.rating >= 0:
            return {"success": False,
                    "msg": "this ride already rated"}, 403
        if rating < 0 or rating > 5:
            return {"success": False,
                    "msg": "the rating must be number from 0 to 5"}, 403
        if not (rating_object.rater_id == user_id):
            return {"success": False,
                    "msg": "cannot rate others ratings"}, 403
        try:
            rating_object.rate(rating, comment)
            response = Response(success=True, message="Rated successfully", status_code=200, )
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
    def get_my_ratings(user_id, ride_id=None):
        user_exists = Users.get_by_id(user_id)
        if not user_exists:
            return {"success": False,
                    "msg": "This user does not exist."}, 404
        try:
            my_ratings = RatingRequest.get_pending_ratings(user_id, ride_id)
            response = Response(success=True, message="get my ratings successfully", status_code=200,
                                data={"my_ratings": my_ratings})
            return response.to_tuple()
        except Exception as e:
            return {"success": False,
                    "msg": "cannot get user comments: " + str(e)}, 403

    @staticmethod
    def remove_rating(user_id, rating_id):
        rating_object = RatingRequest.get_by_id(rating_id)
        if not rating_object:
            return {"success": False,
                    "msg": "This rating does not exist."}, 404
        if rating_object.rating >= 0:
            return {"success": False,
                    "msg": "this ride already rated"}, 403
        if not (rating_object.rater_id == user_id):
            return {"success": False,
                    "msg": "cannot rate others ratings"}, 403
        try:
            rating_object.remove()
            response = Response(success=True, message="the rating removed successfully", status_code=200)
            return response.to_tuple()
        except Exception as e:
            return {"success": False,
                    "msg": "failed to remove the rating"}, 403
