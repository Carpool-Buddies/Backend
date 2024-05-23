import pytest
from math import isclose

from api.config import BaseConfig
from utils.map_service import MapsService

def test_haversine():
    service = MapsService()
    lat1, lon1 = 37.7749, -122.4194  # San Francisco
    lat2, lon2 = 34.0522, -118.2437  # Los Angeles
    distance = service.haversine(lat1, lon1, lat2, lon2)
    expected_distance = 559  # approximate distance in kilometers
    assert isclose(distance, expected_distance, rel_tol=0.01)

def test_distance_matrix_with_haversine():
    service = MapsService()
    origins = ["37.7749,-122.4194"]
    destinations = ["34.0522,-118.2437"]
    result = service.distance_matrix(origins, destinations, mode='driving')
    distance = result['rows'][0]['elements'][0]['distance']['value'] / 1000  # convert to kilometers
    expected_distance = 559  # approximate distance in kilometers
    assert isclose(distance, expected_distance, rel_tol=0.01)

@pytest.mark.parametrize("origins, destinations", [
    (["37.7749,-122.4194"], ["34.0522,-118.2437"]),
    (["40.7128,-74.0060"], ["34.0522,-118.2437"]),
])
def test_distance_matrix_with_google_maps_api(monkeypatch, origins, destinations):
    class MockGoogleMapsClient:
        def distance_matrix(self, origins, destinations, mode):
            return {
                'rows': [{
                    'elements': [{
                        'status': 'OK',
                        'distance': {'value': 1000000}  # 1000 km for simplicity
                    }]
                }]
            }

    service = MapsService(api_key=BaseConfig.GOOGLE_MAPS_API_KEY)
    monkeypatch.setattr(service, 'client', MockGoogleMapsClient())
    result = service.distance_matrix(origins, destinations, mode='driving')
    distance = result['rows'][0]['elements'][0]['distance']['value'] / 1000  # convert to kilometers
    assert distance == 1000  # check if the mock distance is returned correctly