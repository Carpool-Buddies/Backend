import re
import googlemaps
from api.config import BaseConfig

gmaps = googlemaps.Client(key=BaseConfig.GOOGLE_MAPS_API_KEY)

def parse_location(location_str):
    """
    Parses a location string in the format "latitude,longitude".

    Parameters:
    - location_str: str, the location string to parse

    Returns:
    - tuple: (lat, lng) if valid, else raises ValueError
    """
    pattern = r"^-?\d+\.\d+,-?\d+\.\d+$"
    if not re.match(pattern, location_str):
        raise ValueError("Invalid location format. Expected format: 'latitude,longitude'")

    try:
        lat, lng = map(float, location_str.split(','))
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            raise ValueError("Invalid latitude or longitude values")
        return lat, lng
    except Exception as e:
        raise ValueError(f"Error parsing location: {str(e)}")

def calculate_distance(origin, destination):
    """
    Calculates the driving distance between two locations using Google Maps API.

    Parameters:
    - origin: tuple, (lat, lng) of the origin
    - destination: tuple, (lat, lng) of the destination

    Returns:
    - float: distance in kilometers if valid, else raises ValueError
    """
    try:
        origin_str = f"{origin[0]},{origin[1]}"
        destination_str = f"{destination[0]},{destination[1]}"
        distance_result = gmaps.distance_matrix(origins=[origin_str], destinations=[destination_str], mode='driving')
        if distance_result['rows'][0]['elements'][0]['status'] == 'OK':
            distance = distance_result['rows'][0]['elements'][0]['distance']['value']
            return distance / 1000  # distance in kilometers
        else:
            raise ValueError("Invalid response from Google Maps API")
    except Exception as e:
        raise ValueError(f"Error calculating distance: {str(e)}")
