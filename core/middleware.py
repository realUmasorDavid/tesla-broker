from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings

class AccessCodeMiddleware:
    """
    Forces new users to enter a valid access code before accessing the site
    (except login, access_code, register, static files, etc.)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for certain paths
        exempt_paths = [
            reverse('login'),
            reverse('access_code'),
            # reverse('register'),
            '/admin/',
            '/static/',
            '/media/',
            reverse('verify_email'),
        ]

        if any(request.path.startswith(path) for path in exempt_paths):
            return self.get_response(request)

        # If user is authenticated → allow
        if request.user.is_authenticated:
            return self.get_response(request)

        # Check session for access grant
        if not request.session.get('access_granted'):
            return HttpResponseRedirect(reverse('access_code'))

        return self.get_response(request)