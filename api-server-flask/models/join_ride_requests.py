from . import db
from datetime import datetime

class JoinRideRequests(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    passenger_id = db.Column(db.Integer, nullable=False)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<JoinRideRequests passenger_id={self.passenger_id} ride_id={self.ride_id} status={self.status}>"
