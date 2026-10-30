class DisableClientCacheMiddleware:
    """
    Middleware to prevent client-side browser caching (bfcache) for authenticated users 
    and sensitive authentication pages (login, register, logout, etc.).
    
    This ensures that when a user logs in and presses the browser back button, 
    the browser does not load a stale snapshot from cache, but instead re-contacts 
    the server (which redirects authenticated users to their proper destination).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Paths that should never be cached in browser history
        auth_paths = (
            '/login/',
            '/register/',
            '/logout/',
            '/forgot-password/',
            '/verify-reset-code/',
            '/reset-password/',
            '/dashboard/',
            '/profile/',
        )

        should_disable_cache = (
            request.user.is_authenticated or 
            any(request.path.startswith(path) for path in auth_paths)
        )

        if should_disable_cache:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response
