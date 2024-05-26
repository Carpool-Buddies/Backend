# import pytest
# from datetime import datetime, timedelta
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from models import Rides, db
# from services.specifications import *
#
# Base = db.Model
#
# # Create an in-memory SQLite database for testing
# engine = create_engine('sqlite:///:memory:', echo=True)
# Session = sessionmaker(bind=engine)
#
# # Create the table
# Base.metadata.create_all(engine)
#
# # Sample data for testing
# ride1 = Rides(id=1, departure_datetime=datetime(2023, 5, 26, 10, 0), available_seats=4, status='waiting', driver_id=1)
# ride2 = Rides(id=2, departure_datetime=datetime(2023, 5, 26, 12, 0), available_seats=2, status='confirmed', driver_id=2)
# ride3 = Rides(id=3, departure_datetime=datetime(2023, 5, 26, 15, 0), available_seats=1, status='waiting', driver_id=3)
#
# @pytest.fixture
# def session():
#     session = Session()
#     session.add_all([ride1, ride2, ride3])
#     session.commit()
#     yield session
#     session.close()
#
# def test_and_specification(session):
#     spec1 = AvailableSeatsSpecification(2)
#     spec2 = RideStatusSpecification('waiting')
#     and_spec = AndSpecification(spec1, spec2)
#
#     query = session.query(Rides)
#     filtered_query = and_spec.apply(query)
#     rides = filtered_query.all()
#
#     assert len(rides) == 2
#     assert rides[0].id == 1
#     assert rides[1].id == 3
#
# def test_available_seats_specification(session):
#     spec = AvailableSeatsSpecification(3)
#
#     query = session.query(Rides)
#     filtered_query = spec.apply(query)
#     rides = filtered_query.all()
#
#     assert len(rides) == 2
#     assert rides[0].id == 1
#     assert rides[1].id == 2
#
# def test_departure_date_specification(session):
#     spec = DepartureDateSpecification(datetime(2023, 5, 26, 11, 0), delta_hours=2)
#
#     query = session.query(Rides)
#     filtered_query = spec.apply(query)
#     rides = filtered_query.all()
#
#     assert len(rides) == 2
#     assert rides[0].id == 1
#     assert rides[1].id == 2
#
# def test_ride_status_specification(session):
#     spec = RideStatusSpecification('waiting')
#
#     query = session.query(Rides)
#     filtered_query = spec.apply(query)
#     rides = filtered_query.all()
#
#     assert len(rides) == 2
#     assert rides[0].id == 1
#     assert rides[1].id == 3
#
# def test_not_my_ride_specification(session):
#     spec = NotMyRideSpecification(1)
#
#     query = session.query(Rides)
#     filtered_query = spec.apply(query)
#     rides = filtered_query.all()
#
#     assert len(rides) == 2
#     assert rides[0].id == 2
#     assert rides[1].id == 3