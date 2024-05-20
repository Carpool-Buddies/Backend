import pytz

from . import db
from datetime import datetime


class JoinRideRequests(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    passenger_id = db.Column(db.Integer, nullable=False)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone('Israel')))

    def __repr__(self):
        return f"<JoinRideRequests passenger_id={self.passenger_id} ride_id={self.ride_id} status={self.status}>"


    def save(self):
        db.session.add(self)
        db.session.commit()


    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)

    def to_dict(self):
        ride_dict = {
            'passenger_id': self.passenger_id,
            'ride_id': self.ride_id,
            '_created_at': self.created_at.isoformat()
        }
        return ride_dict

    def to_json(self):
        return self.to_dict()
