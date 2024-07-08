import pytz
from sqlalchemy import UniqueConstraint

from models import db
from utils.response import Response
from . import Rides
from datetime import datetime


class JoinRideRequests(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    passenger_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    requested_seats = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    __table_args__ = (
        UniqueConstraint('ride_id', 'passenger_id', name='uq_ride_passenger'),
    )

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

    @staticmethod
    def delete_not_accepted_passengers():
        # Calculate the cutoff time (4 minutes ago from the current time)
        from api import app
        with app.app_context():
            # Delete expired verification codes directly from the database
            result = db.session.query(JoinRideRequests.id).join(
                Rides, Rides.id == JoinRideRequests.ride_id
            ).filter(
                JoinRideRequests.status != 'accepted',
                Rides.departure_datetime < datetime.now()
            ).all()
            ids_to_delete = [row.id for row in result]
            db.session.query(JoinRideRequests).filter(
                JoinRideRequests.id.in_(ids_to_delete)
            ).delete(synchronize_session=False)
            # Commit the changes to the database
            db.session.commit()
        response = Response(success=True, message="OK", status_code=200)
        return response.to_tuple()


