from django.http import HttpResponseRedirect
from django.urls import reverse

class AccessCodeMiddleware:
    """
    Only the register page requires a valid access code.
    Login, index, and other pages are freely accessible.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Paths that are always allowed
        exempt_paths = [
            reverse('login'),
            reverse('access_code'),
            reverse('index'),
            '/admin/',
            '/static/',
            '/media/',
        ]

        if any(request.path.startswith(p) for p in exempt_paths):
            return self.get_response(request)

        # Only protect the register page
        if request.path == reverse('register'):
            if not request.session.get('access_granted'):
                return HttpResponseRedirect(reverse('access_code'))

        return self.get_response(request)