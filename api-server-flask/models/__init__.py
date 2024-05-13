from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy db instance
db = SQLAlchemy()

# Import the models after initializing db to avoid circular imports
from .users import Users
from .rides import Rides
from .join_ride_requests import JoinRideRequests
from .jwt_token_blocklist import JWTTokenBlocklist
from .ride_offers import RideOffers
from .verification_codes import VerificationCodes
