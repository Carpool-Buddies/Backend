from datetime import datetime
# from join_ride_requests import JoinRideRequests
from utils.response import Response
from . import db
from .join_ride_requests import JoinRideRequests


class Rides(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='waiting')
    departure_location = db.Column(db.String(100), nullable=False)
    pickup_radius = db.Column(db.Float, nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    drop_radius = db.Column(db.Float, nullable=False)
    departure_datetime = db.Column(db.DateTime, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    confirmed_passengers = db.Column(db.Integer, nullable=False, default=0)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return f"Ride {self.id}"

    def save(self):
        db.session.add(self)
        db.session.commit()

    def update_details(self, new_details):
        """
        Updates the ride details with new information.

        Parameters:
        - new_details: dict, a dictionary containing the updated details for the ride

        Returns:
        - success: bool, indicates whether the ride details update was successful
        """
        try:
            for key, value in new_details.items():
                if key == "departure_datetime":
                    value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
                setattr(self, key, value)
            self.save()
            return True
        except Exception as e:
            print(f"Error updating ride details: {str(e)}")
            db.session.rollback()
            return False

    def start_ride(self):
        """
        Starts the ride by setting the status to 'InProgress'.
        """
        try:
            self.status = 'InProgress'
            self.save()
        except Exception as e:
            print(f"Error starting ride: {str(e)}")
            db.session.rollback()
            return False
        return True

    def end_ride(self):
        """
        Ends the ride by setting the status to 'Completed'.
        """
        try:
            self.status = 'Completed'
            self.save()
        except Exception as e:
            print(f"Error ending ride: {str(e)}")
            db.session.rollback()
            return False
        return True

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)

    def to_dict(self):
        ride_dict = {
            'ride_id': self.id,
            '_driver_id': self.driver_id,
            '_departure_location': self.departure_location,
            '_pickup_radius': self.pickup_radius,
            '_destination': self.destination,
            '_drop_radius': self.drop_radius,
            '_departure_datetime': self.departure_datetime.isoformat(),
            '_available_seats': self.available_seats,
            '_confirmed_passengers': self.confirmed_passengers,
            '_notes': self.notes,
            '_created_at': self.created_at.isoformat(),
            '_status': self.status
        }
        return ride_dict

    def to_json(self):
        return self.to_dict()

    # TODO: Issues-18
    def accept_ride_request(self, request_id):
        """
        Accepts a ride request for this ride.

        Parameters:
        - request_id: int, the ID of the ride request to accept

        Returns:
        - success: bool, indicates whether the request was accepted successfully
        """
        try:
            # Retrieve the ride request by ID
            from . import JoinRideRequests
            ride_request = JoinRideRequests.query.get_or_404(request_id)

            # Ensure the request is for this ride
            if ride_request.ride_id != self.id:
                return False

            # Update the status of the ride request to accepted
            ride_request.status = 'accepted'
            self.confirmed_passengers += 1  # Increment confirmed passengers

            db.session.commit()
            return True
        except Exception as e:
            print(f"Error accepting ride request: {str(e)}")
            db.session.rollback()
            return False

    def reject_ride_request(self, request_id):
        """
        Rejects a ride request for this ride.

        Parameters:
        - request_id: int, the ID of the ride request to reject

        Returns:
        - success: bool, indicates whether the request was rejected successfully
        """
        try:
            # Retrieve the ride request by ID
            from . import JoinRideRequests
            ride_request = JoinRideRequests.query.get_or_404(request_id)

            # Ensure the request is for this ride
            if ride_request.ride_id != self.id:
                return False

            # Update the status of the ride request to rejected
            ride_request.status = 'rejected'

            db.session.commit()
            return True
        except Exception as e:
            print(f"Error rejecting ride request: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def delete_not_started_rides():
        # Calculate the cutoff time (4 minutes ago from the current time)
        from api import app
        cutoff_time = datetime.now()
        with app.app_context():
            # Delete expired verification codes directly from the database
            x = Rides.query.filter(Rides.departure_datetime < cutoff_time, Rides.status != 'waiting')
            x.delete(synchronize_session=False)

            # Commit the changes to the database
            db.session.commit()
        response = Response(success=True, message="OK", status_code=200)
        return response.to_tuple()
