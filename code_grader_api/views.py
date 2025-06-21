from django.http import JsonResponse
from django.views.defaults import page_not_found
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_404_handler(request, exception=None):
    """
    Custom 404 handler that returns JSON response for API endpoints
    """
    # Log the 404 error
    logger.warning(f"404 Not Found: {request.method} {request.path} - User Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
    
    # Check if it's an API request
    if request.path.startswith('/api/'):
        return JsonResponse({
            "error": "Endpoint not found",
            "message": f"The requested endpoint '{request.path}' does not exist",
            "status": "404",
            "available_endpoints": {
                "evaluation": "/api/evaluation/",
                "analytics": "/api/analytics/",
                "metrics": "/api/metrics/",
                "admin": "/admin/"
            },
            "suggestions": [
                "Check the URL spelling",
                "Verify the endpoint exists in the API documentation",
                "Ensure you're using the correct HTTP method",
                "Check if the endpoint requires authentication"
            ]
        }, status=status.HTTP_404_NOT_FOUND)
    
    # For non-API requests, return a simple JSON response
    return JsonResponse({
        "error": "Page not found",
        "message": f"The requested page '{request.path}' does not exist",
        "status": "404"
    }, status=status.HTTP_404_NOT_FOUND)

def custom_500_handler(request, exception=None):
    """
    Custom 500 handler that returns JSON response
    """
    # Log the 500 error
    logger.error(f"500 Internal Server Error: {request.method} {request.path} - Exception: {str(exception) if exception else 'Unknown'}")
    
    return JsonResponse({
        "error": "Internal server error",
        "message": "An unexpected error occurred on the server",
        "status": "500",
        "request_id": getattr(request, 'id', 'unknown')
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def custom_400_handler(request, exception=None):
    """
    Custom 400 handler that returns JSON response
    """
    # Log the 400 error
    logger.warning(f"400 Bad Request: {request.method} {request.path} - Exception: {str(exception) if exception else 'Unknown'}")
    
    return JsonResponse({
        "error": "Bad request",
        "message": "The request could not be processed due to invalid syntax",
        "status": "400",
        "details": str(exception) if exception else "Invalid request format"
    }, status=status.HTTP_400_BAD_REQUEST)

def custom_403_handler(request, exception=None):
    """
    Custom 403 handler that returns JSON response
    """
    # Log the 403 error
    logger.warning(f"403 Forbidden: {request.method} {request.path} - Exception: {str(exception) if exception else 'Unknown'}")
    
    return JsonResponse({
        "error": "Forbidden",
        "message": "You don't have permission to access this resource",
        "status": "403"
    }, status=status.HTTP_403_FORBIDDEN) 