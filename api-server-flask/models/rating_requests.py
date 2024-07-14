from datetime import datetime
# from join_ride_requests import JoinRideRequests
from sqlalchemy import UniqueConstraint, case
from sqlalchemy.sql import func
from utils.response import Response
from . import db, Users


class RatingRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rater_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rated_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=-1)
    comments = db.Column(db.Text, nullable=True, default="")

    __table_args__ = (
        UniqueConstraint('rater_id', 'rated_id', 'ride_id', name='uq_ride_rating'),
    )

    def save(self):
        db.session.add(self)
        db.session.commit()

    def remove(self):
        db.session.delete(self)
        db.session.commit()

    def update_field(self, field, value):
        if hasattr(self, field):
            setattr(self, field, value)
            self.save()
        else:
            raise AttributeError("Invalid field name.")

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)

    @staticmethod
    def create_rating_requests(ride, requests):
        for r in requests:
            print(r)
            rating = RatingRequest(rater_id=r["passenger_id"], rated_id=ride.driver_id, ride_id=ride.id)
            rating.save()
            rating = RatingRequest(rater_id=ride.driver_id, rated_id=r["passenger_id"], ride_id=ride.id)
            rating.save()

    def rate(self, rating, comment):
        self.update_field("rating", rating)
        self.update_field("comments", comment)

    @staticmethod
    def get_average_rating(user_id):
        avg_rating = db.session.query(func.avg(RatingRequest.rating).label('average')).filter(RatingRequest.rated_id==user_id).scalar()

        # Return the average rating if found, otherwise return the default rating of 3.0
        return avg_rating if avg_rating is not None else 3.0

    @staticmethod
    def get_comments(user_id):
        results = db.session.query(
            RatingRequest,
            Users.first_name,
            Users.last_name,
            Users.approved
        ).join(
            Users, RatingRequest.rater_id == Users.id
        ).filter(
            RatingRequest.rated_id == user_id,
            RatingRequest.rating >= 0
        ).all()
        ratings_list = []
        rating = 0
        for rating_request, rater_first_name, rater_last_name, rater_approve in results:

            ratings_list.append({
                "rater_first_name": rater_first_name,
                "rater_last_name": rater_last_name,
                "rater_id": rating_request.rater_id,
                "rating": rating_request.rating,
                "comments": rating_request.comments,
                "rater_approve": rater_approve
            } )
            rating+=rating_request.rating
        rating = 3 if len(ratings_list)== 0 else rating/len(ratings_list)
        return {"ratings_list":ratings_list,"rating":rating,"num_of_raters":len(ratings_list) }

    @staticmethod
    def get_pending_ratings(user_id, ride_id=None):
        query = db.session.query(
            RatingRequest.id,
            RatingRequest.ride_id,
            RatingRequest.rated_id,
            Users.first_name,
            Users.last_name,
            Users.approved
        ).join(
            Users, RatingRequest.rated_id == Users.id
        ).filter(
            RatingRequest.rater_id == user_id,
            RatingRequest.rating == -1
        )

        if ride_id is not None:
            query = query.filter(RatingRequest.ride_id == ride_id)

        results = query.all()

        pending_ratings_list = [{
            "rating_id": rating_id,
            "ride_id": ride_id,
            "user_id": user_id,
            "rated_first_name": rated_first_name,
            "rated_last_name": rated_last_name,
            "rated_approve": rated_approve
        } for rating_id, ride_id, user_id, rated_first_name, rated_last_name, rated_approve in results]

        return pending_ratings_list
