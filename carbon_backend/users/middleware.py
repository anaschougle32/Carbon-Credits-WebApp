from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from re import compile

class ApprovalMiddleware:
    """
    Middleware to handle authentication and redirects.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Compile the public URL patterns that don't require authentication
        self.public_urls = compile(r'^/(?:login|logout|register|api|admin|static|media).*$')
        
    def __call__(self, request):
        # Skip check for unauthenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)
            
        # Skip check for super admins and bank admins
        if request.user.is_super_admin or request.user.is_bank_admin:
            return self.get_response(request)
            
        # Skip check for public URLs
        if self.public_urls.match(request.path):
            return self.get_response(request)
            
        # User is authenticated, continue with the request
        return self.get_response(request) 