import logging
import time

logger = logging.getLogger('api')


class APILoggingMiddleware:
    """Middleware to log details of all API requests to api.log."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only process paths starting with /api/
        if not request.path.startswith('/api/'):
            return self.get_response(request)

        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time

        # Extract request and response metadata
        method = request.method
        path = request.path
        status_code = response.status_code
        ip = request.META.get('REMOTE_ADDR')

        # Log details to the dedicated API file handler
        logger.info(f"[{method}] {path} - Status: {status_code} - Duration: {duration:.3f}s - IP: {ip}")

        return response
