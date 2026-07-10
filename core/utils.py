import ipaddress

import requests


def get_client_ip(request):
    """Get real client IP address (Fly.io proxy, then standard forwarded headers)."""
    fly_ip = request.META.get('HTTP_FLY_CLIENT_IP')
    if fly_ip:
        return fly_ip.strip()

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()

    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip.strip()

    return request.META.get('REMOTE_ADDR', '')


def _is_public_ip(ip):
    try:
        return ipaddress.ip_address(ip).is_global
    except ValueError:
        return False


def _format_location(city='', region='', country=''):
    city = (city or '').strip()
    region = (region or '').strip()
    country = (country or '').strip()
    if city and country:
        return f'{city}, {country}'
    if region and country:
        return f'{region}, {country}'
    return country or None


def _location_from_ip_api(ip):
    response = requests.get(
        f'https://ip-api.com/json/{ip}',
        params={'fields': 'status,message,country,city,regionName'},
        timeout=3,
    )
    if response.status_code != 200:
        return None
    data = response.json()
    if data.get('status') != 'success':
        return None
    return _format_location(
        city=data.get('city'),
        region=data.get('regionName'),
        country=data.get('country'),
    )


def _location_from_ipwho(ip):
    response = requests.get(f'https://ipwho.is/{ip}', timeout=3)
    if response.status_code != 200:
        return None
    data = response.json()
    if not data.get('success'):
        return None
    return _format_location(
        city=data.get('city'),
        region=data.get('region'),
        country=data.get('country'),
    )


def get_location_from_ip(request):
    """Get approximate location from client IP."""
    ip = get_client_ip(request)
    if not ip or not _is_public_ip(ip):
        return 'Unknown Location'

    for lookup in (_location_from_ip_api, _location_from_ipwho):
        try:
            location = lookup(ip)
            if location:
                return location
        except requests.RequestException:
            continue

    return 'Unknown Location'
