from math import radians, sin, cos, sqrt, atan2

class MapsService:
    def __init__(self, api_key=None):
        self.api_key = api_key
        if self.api_key:
            import googlemaps
            self.client = googlemaps.Client(key=self.api_key)
        else:
            self.client = None

    def distance_matrix(self, origins, destinations, mode):
        if self.client:
            # Use the actual Google Maps API client
            return self.client.distance_matrix(origins=origins, destinations=destinations, mode=mode)
        else:
            # Use the Haversine formula for distance calculation
            origin = origins[0].split(',')
            destination = destinations[0].split(',')

            lat1, lon1 = float(origin[0]), float(origin[1])
            lat2, lon2 = float(destination[0]), float(destination[1])

            # Calculate the distance using the Haversine formula
            distance_km = self.haversine(lat1, lon1, lat2, lon2)

            return {
                'rows': [{
                    'elements': [{
                        'status': 'OK',
                        'distance': {'value': distance_km * 1000}  # convert to meters
                    }]
                }]
            }

    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Radius of the Earth in kilometers
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c
        return distance
