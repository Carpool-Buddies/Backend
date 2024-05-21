from datetime import datetime
from utils.maps import geocode_location, calculate_distance
from sqlalchemy.orm import Query
from models import Rides, db


class Specification:
    def is_satisfied_by(self, item) -> bool:
        pass

    def apply(self, query: Query):
        pass


class DepartureDateSpecification(Specification):
    def __init__(self, departure_date: datetime):
        self.departure_date = departure_date

    def is_satisfied_by(self, item) -> bool:
        return item.departure_datetime.date() == self.departure_date.date()

    def apply(self, query: Query):
        return query.filter(db.func.date(Rides.departure_datetime) == self.departure_date.date())

class AndSpecification(Specification):
    def __init__(self, *specifications):
        self.specifications = specifications

    def is_satisfied_by(self, item) -> bool:
        return all(spec.is_satisfied_by(item) for spec in self.specifications)

    def apply(self, query: Query):
        for spec in self.specifications:
            query = spec.apply(query)
        return query

class DepartureLocationSpecification(Specification):
    def __init__(self, departure_location: str, pickup_radius: float):
        self.departure_location = departure_location
        self.pickup_radius = pickup_radius
        self.lat, self.lng = geocode_location(departure_location)

    def is_satisfied_by(self, item) -> bool:
        item_lat, item_lng = geocode_location(item.departure_location)
        distance = calculate_distance((self.lat, self.lng), (item_lat, item_lng))
        return distance <= self.pickup_radius * 1000

    def apply(self, query: Query):
        rides = query.all()
        filtered_rides = [ride for ride in rides if self.is_satisfied_by(ride)]
        return filtered_rides


class DestinationSpecification(Specification):
    def __init__(self, destination: str, drop_radius: float):
        self.destination = destination
        self.drop_radius = drop_radius
        self.lat, self.lng = geocode_location(destination)

    def is_satisfied_by(self, item) -> bool:
        item_lat, item_lng = geocode_location(item.destination)
        distance = calculate_distance((self.lat, self.lng), (item_lat, item_lng))
        return distance <= self.drop_radius * 1000

    def apply(self, query: Query):
        rides = query.all()
        filtered_rides = [ride for ride in rides if self.is_satisfied_by(ride)]
        return filtered_rides

class AvailableSeatsSpecification(Specification):
    def __init__(self, available_seats: int):
        self.available_seats = available_seats

    def is_satisfied_by(self, item) -> bool:
        return item.available_seats >= self.available_seats

    def apply(self, query: Query):
        return query.filter(Rides.available_seats >= self.available_seats)