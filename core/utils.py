import requests
from django.utils import timezone

def get_client_ip(request):
    """Get real client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_location_from_ip(request):
    """Get approximate location (free service)"""
    ip = get_client_ip(request)
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=3)
        if response.status_code == 200:
            data = response.json()
            city = data.get('city', 'Unknown')
            country = data.get('country_name', 'Unknown')
            return f"{city}, {country}" if city != 'Unknown' else country
    except:
        pass
    return "Unknown Location"