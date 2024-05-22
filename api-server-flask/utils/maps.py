from api.config import BaseConfig
from utils.map_service import MapsService

# Initialize the MapsService with or without the API key
gmaps = MapsService(api_key=BaseConfig.GOOGLE_MAPS_API_KEY)

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
