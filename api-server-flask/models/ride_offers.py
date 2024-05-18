import datetime
from . import db


class RideOffers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    passenger_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    departure_location = db.Column(db.String(100), nullable=False)
    pickup_radius = db.Column(db.Float, nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    drop_radius = db.Column(db.Float, nullable=False)
    departure_datetime = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return f"RideOffer {self.id}"

    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)

    def to_dict(self):
        ride_dict = {
            '_passenger_id': self.driver_id,
            '_departure_location': self.departure_location,
            '_pickup_radius': self.pickup_radius,
            '_destination': self.destination,
            '_drop_radius': self.drop_radius,
            '_departure_datetime': self.departure_datetime.isoformat(),
            '_notes': self.notes,
            '_created_at': self.created_at.isoformat()
        }
        return ride_dict

    def to_json(self):
        return self.to_dict()
