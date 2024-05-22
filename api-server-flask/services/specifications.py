from utils.maps import calculate_distance, parse_location
from sqlalchemy.orm import Query
from models import Rides
from datetime import datetime, timedelta


class Specification:
    def is_satisfied_by(self, item) -> bool:
        pass

    def apply(self, query: Query):
        pass

class AndSpecification(Specification):
    def __init__(self, *specifications):
        self.specifications = specifications

    def is_satisfied_by(self, item) -> bool:
        return all(spec.is_satisfied_by(item) for spec in self.specifications)

    def apply(self, query: Query):
        for spec in self.specifications:
            query = spec.apply(query)
        return query

class AvailableSeatsSpecification(Specification):
    def __init__(self, available_seats: int):
        self.available_seats = available_seats

    def is_satisfied_by(self, item) -> bool:
        return item.available_seats >= self.available_seats

    def apply(self, query: Query):
        return query.filter(Rides.available_seats >= self.available_seats)

class DepartureLocationSpecification(Specification):
    def __init__(self, departure_location: str, pickup_radius: float):
        self.departure_location = departure_location
        self.pickup_radius = pickup_radius
        self.lat, self.lng = parse_location(departure_location)

    def is_satisfied_by(self, item) -> bool:
        item_lat, item_lng = parse_location(item.departure_location)
        distance = calculate_distance((self.lat, self.lng), (item_lat, item_lng))
        return distance <= self.pickup_radius

    def apply(self, query: Query):
        rides = query.all()
        filtered_rides = [ride for ride in rides if self.is_satisfied_by(ride)]
        return filtered_rides

class DestinationLocationSpecification(Specification):
    def __init__(self, destination: str, drop_radius: float):
        self.destination = destination
        self.drop_radius = drop_radius
        self.lat, self.lng = parse_location(destination)

    def is_satisfied_by(self, item) -> bool:
        item_lat, item_lng = parse_location(item.destination)
        distance = calculate_distance((self.lat, self.lng), (item_lat, item_lng))
        return distance <= self.drop_radius

    def apply(self, query: Query):
        rides = query.all()
        filtered_rides = [ride for ride in rides if self.is_satisfied_by(ride)]
        return filtered_rides

class DepartureDateSpecification(Specification):
    def __init__(self, departure_datetime: datetime):
        self.departure_datetime = departure_datetime

    def is_satisfied_by(self, item) -> bool:
        current_time = datetime.utcnow()
        lower_bound = max(self.departure_datetime - timedelta(hours=5), current_time)
        upper_bound = self.departure_datetime + timedelta(hours=5)
        return lower_bound <= item.departure_datetime <= upper_bound

    def apply(self, query: Query):
        current_time = datetime.utcnow()
        lower_bound = max(self.departure_datetime - timedelta(hours=5), current_time)
        upper_bound = self.departure_datetime + timedelta(hours=5)
        return query.filter(
            Rides.departure_datetime.between(lower_bound, upper_bound)
        )

class RideStatusSpecification(Specification):
    def __init__(self, status: str = 'waiting'):
        self.status = status

    def is_satisfied_by(self, item) -> bool:
        return item.status == self.status

    def apply(self, query: Query):
        return query.filter(Rides.status == self.status)