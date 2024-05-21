import googlemaps
from api.config import BaseConfig

gmaps = googlemaps.Client(key=BaseConfig.GOOGLE_MAPS_API_KEY)

def geocode_location(address):
    geocode_result = gmaps.geocode(address)
    if geocode_result:
        location = geocode_result[0]['geometry']['location']
        return location['lat'], location['lng']
    return None, None

def calculate_distance(origin, destination):
    distance_result = gmaps.distance_matrix(origins=[origin], destinations=[destination], mode='driving')
    if distance_result['rows'][0]['elements'][0]['status'] == 'OK':
        distance = distance_result['rows'][0]['elements'][0]['distance']['value']
        return distance  # distance in meters
    return None