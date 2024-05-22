import pytest
from utils.map_service import MapsService
from api.config import BaseConfig

@pytest.mark.integration
def test_google_maps_api_connection():
    if not BaseConfig.GOOGLE_MAPS_API_KEY:
        pytest.skip("Google Maps API key not provided")

    service = MapsService(api_key=BaseConfig.GOOGLE_MAPS_API_KEY)
    origins = ["37.7749,-122.4194"]  # San Francisco
    destinations = ["34.0522,-118.2437"]  # Los Angeles

    try:
        result = service.distance_matrix(origins, destinations, mode='driving')
        assert 'rows' in result
        assert 'elements' in result['rows'][0]
        assert result['rows'][0]['elements'][0]['status'] == 'OK'
        assert 'distance' in result['rows'][0]['elements'][0]
        # print(f"Distance: {result['rows'][0]['elements'][0]['distance']['text']}")
    except Exception as e:
        pytest.fail(f"Google Maps API request failed: {e}")


