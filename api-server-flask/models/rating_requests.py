from datetime import datetime
# from join_ride_requests import JoinRideRequests
from utils.response import Response
from . import db


class RatingRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rater_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rated_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False,default=-1)
    comments = db.Column(db.Text, nullable=True,default="")




    def save(self):
        db.session.add(self)
        db.session.commit()

    def update_field(self, field, value):
        if hasattr(self, field):
            setattr(self, field, value)
            self.save()
        else:
            raise AttributeError("Invalid field name.")

    @staticmethod
    def create_rating_requests(ride,requests):
        for r in requests:
            rating = RatingRequest(rater_id=r.passenger_id,rated_id=ride.driver_id,ride_id=ride.id)
            rating.save()
            rating = RatingRequest(rater_id=ride.driver_id,rated_id=r.passenger_id,ride_id=ride.id)
            rating.save()
