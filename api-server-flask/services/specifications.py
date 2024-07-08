from sqlalchemy.orm import Query
from sqlalchemy import func, cast, types
from models import Rides
from datetime import datetime, timedelta

from utils.location_utils import parse_location
from utils.maps import calculate_distance
import geocoder


class Specification:
    def is_satisfied_by(self, item) -> bool:
        raise NotImplementedError

    def apply(self, query: Query):
        raise NotImplementedError


class AndSpecification(Specification):
    def __init__(self, *specifications):
        self.specifications = specifications

    def is_satisfied_by(self, item) -> bool:
        return all(spec.is_satisfied_by(item) for spec in self.specifications)

    def apply(self, query: Query) -> Query:
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


# TODO: Try to do this in query
class DepartureLocationSpecification(Specification):
    def __init__(self, departure_location: str, pickup_radius: float):
        self.departure_location = departure_location
        self.pickup_radius = pickup_radius
        self.location = self.geocode_location(departure_location)

    def geocode_location(self, location_str):
        """
        Use a geocoding service to convert a location string to latitude and longitude.
        """
        g = geocoder.google(location_str)
        if g.ok:
            return g.latlng
        else:
            raise ValueError(f"Unable to geocode location: {location_str}")

    def is_satisfied_by(self, item) -> bool:
        item_location = self.geocode_location(item.departure_location)
        distance = calculate_distance(self.location, item_location)
        return distance <= self.pickup_radius

    def apply(self, query: Query) -> Query:
        point = func.ST_GeomFromText(f'POINT({self.location[1]} {self.location[0]})', 4326)
        departure_location_point = func.ST_GeomFromText(
            func.concat(
                'POINT(',
                cast(Rides.latitude, types.String),
                ' ',
                cast(Rides.longitude, types.String),
                ')'
            ),
            4326
        )
        return query.filter(
            func.ST_Distance(departure_location_point, point) <= self.pickup_radius * 1000
        )


# TODO: Try to do this in query
class DestinationLocationSpecification(Specification):
    def __init__(self, destination: str, drop_radius: float):
        self.destination = destination
        self.drop_radius = drop_radius
        self.lat, self.lng = parse_location(destination)

    def is_satisfied_by(self, item) -> bool:
        item_lat, item_lng = parse_location(item.destination)
        distance = calculate_distance((self.lat, self.lng), (item_lat, item_lng))
        return distance <= self.drop_radius

    def apply(self, query: Query) -> Query:
        point = func.ST_SetSRID(func.ST_MakePoint(self.lng, self.lat), 4326)
        return query.filter(
            func.ST_DWithin(
                func.ST_SetSRID(func.ST_MakePoint(
                    func.split_part(Rides.destination, ',', 2).cast(func.Float),
                    func.split_part(Rides.destination, ',', 1).cast(func.Float)
                ), 4326),
                point,
                self.drop_radius * 1000
            )
        )


class DepartureDateSpecification(Specification):
    def __init__(self, departure_datetime: datetime, delta_hours: int = 5):
        self.departure_datetime = departure_datetime
        self.delta_hours = delta_hours

    def is_satisfied_by(self, item) -> bool:
        current_time = datetime.now(self.departure_datetime.tzinfo)  # Ensure current_time has the same timezone
        lower_bound = max(self.departure_datetime - timedelta(minutes=int(self.delta_hours*60)), current_time)
        upper_bound = self.departure_datetime + timedelta(minutes=int(self.delta_hours*60))
        return lower_bound <= item.departure_datetime <= upper_bound

    def apply(self, query: Query) -> Query:
        current_time = datetime.now(self.departure_datetime.tzinfo)  # Ensure current_time has the same timezone
        lower_bound = max(self.departure_datetime - timedelta(minutes=int(self.delta_hours*60)), current_time)
        upper_bound = self.departure_datetime + timedelta(minutes=int(self.delta_hours*60))
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


class NotMyRideSpecification(Specification):
    def __init__(self, user_id: int):
        self.user_id = user_id

    def is_satisfied_by(self, item) -> bool:
        return item.driver_id != self.user_id

    def apply(self, query: Query):
        return query.filter(Rides.driver_id != self.user_id)
