import pytz

from . import db
from datetime import datetime

class JoinRideRequests(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    passenger_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    requested_seats = db.Column(db.Integer, nullable=False, default=1)
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
        return {
            "id": self.id,
            "ride_id": self.ride_id,
            "passenger_id": self.passenger_id,
            "status": self.status,
            "requested_seats": self.requested_seats,
            "created_at": self.created_at.isoformat()
        }

    def to_json(self):
        return self.to_dict()
