import pytest

from utils.location_utils import parse_location
from utils.maps import calculate_distance


def test_parse_location_valid():
    location = "37.7749,-122.4194"
    expected = (37.7749, -122.4194)
    result = parse_location(location)
    assert result == expected


def test_parse_location_invalid_format():
    location = "invalid_location"
    with pytest.raises(ValueError, match="Invalid location format. Expected format: 'latitude,longitude'"):
        parse_location(location)


def test_parse_location_invalid_values():
    location = "100.0000,200.0000"
    with pytest.raises(ValueError, match="Invalid latitude or longitude values"):
        parse_location(location)


def test_calculate_distance_with_haversine(monkeypatch):
    class MockMapsService:
        def distance_matrix(self, origins, destinations, mode):
            return {
                'rows': [{
                    'elements': [{
                        'status': 'OK',
                        'distance': {'value': 559000}  # 559 km in meters for testing
                    }]
                }]
            }

    gmaps = MockMapsService()
    monkeypatch.setattr('utils.maps.gmaps', gmaps)

    origin = (37.7749, -122.4194)
    destination = (34.0522, -118.2437)
    expected_distance = 559  # in kilometers

    result = calculate_distance(origin, destination)
    assert result == expected_distance


def test_calculate_distance_with_google_maps_api(monkeypatch):
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

    gmaps = MockGoogleMapsClient()
    monkeypatch.setattr('utils.maps.gmaps', gmaps)

    origin = (37.7749, -122.4194)
    destination = (34.0522, -118.2437)
    expected_distance = 1000  # mock distance

    result = calculate_distance(origin, destination)
    assert result == expected_distance


def test_calculate_distance_api_failure(monkeypatch):
    class MockGoogleMapsClient:
        def distance_matrix(self, origins, destinations, mode):
            return {
                'rows': [{
                    'elements': [{
                        'status': 'NOT_FOUND'
                    }]
                }]
            }

    gmaps = MockGoogleMapsClient()
    monkeypatch.setattr('utils.maps.gmaps', gmaps)

    origin = (37.7749, -122.4194)
    destination = (34.0522, -118.2437)

    with pytest.raises(ValueError, match="Invalid response from Google Maps API"):
        calculate_distance(origin, destination)