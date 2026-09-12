import math
import re
import uuid
from datetime import date, datetime

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points on Earth
    using the Haversine formula.
    Returns distance in kilometers rounded to 2 decimal places.
    """
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    except (TypeError, ValueError):
        return None

    # Earth radius in kilometers
    r = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance = r * c

    return round(distance, 2)


def validate_email(email):
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email.strip()))


def validate_password(password, min_length=6):
    """Validate password meets minimum requirements."""
    if not password or not isinstance(password, str):
        return False
    return len(password) >= min_length


def validate_servings(servings):
    """Servings must be an integer >= 1."""
    try:
        val = int(servings)
        return val >= 1
    except (TypeError, ValueError):
        return False


def validate_budget(budget):
    """Budget must be a non-negative number."""
    try:
        val = float(budget)
        return val >= 0
    except (TypeError, ValueError):
        return False


def validate_uuid(val):
    """Check if value is a valid UUID string or mock-friendly id."""
    if not val:
        return False
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, AttributeError):
        # Support mock identifiers such as 'recipe-001', 'store-1'
        return isinstance(val, str) and len(val.strip()) > 0


def validate_coordinates(lat, lon):
    """Check if latitude and longitude are valid coordinates."""
    try:
        lat = float(lat)
        lon = float(lon)
        return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0
    except (TypeError, ValueError):
        return False
