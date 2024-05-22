import re

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