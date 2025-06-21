"""
Custom middleware for tracking database operations and user activity.
"""

import logging
import time
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

db_logger = logging.getLogger('database_operations')
activity_logger = logging.getLogger('user_activity')


class DatabaseLoggingMiddleware(MiddlewareMixin):
    """Middleware to log all database queries."""
    
    def process_request(self, request):
        """Log the start of request processing."""
        request.start_time = time.time()
        request.db_queries_start = len(connection.queries)
        
        # Log user activity
        user_info = f"User: {request.user.username if request.user.is_authenticated else 'Anonymous'}"
        ip_address = self.get_client_ip(request)
        activity_logger.info(f"Request started - {request.method} {request.path} - {user_info} - IP: {ip_address}")
        
        return None
    
    def process_response(self, request, response):
        """Log the end of request processing with database query info."""
        if hasattr(request, 'start_time'):
            total_time = time.time() - request.start_time
            db_queries_count = len(connection.queries) - getattr(request, 'db_queries_start', 0)
            
            # Log database operations
            if db_queries_count > 0:
                db_logger.info(f"Request: {request.method} {request.path} - DB Queries: {db_queries_count} - Time: {total_time:.3f}s")
                
                # Log individual queries if there are many
                if db_queries_count > 5:
                    for i, query in enumerate(connection.queries[-db_queries_count:], 1):
                        query_time = float(query['time']) if query['time'] else 0.0
                        db_logger.debug(f"Query {i}: {query['sql'][:100]}... (Time: {query_time:.3f}s)")
            
            # Log user activity completion
            status_code = response.status_code
            activity_logger.info(f"Request completed - {request.method} {request.path} - Status: {status_code} - Time: {total_time:.3f}s")
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ActivityLoggingMiddleware(MiddlewareMixin):
    """Middleware to log user activities in GitHub-style format."""
    
    def process_request(self, request):
        """Log user activity at request start."""
        if request.path.startswith('/api/'):
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
            referer = request.META.get('HTTP_REFERER', 'Direct')
            
            activity_logger.info(f"API Access - {request.method} {request.path} - Agent: {user_agent[:50]} - Referer: {referer[:50]}")
        
        return None
    
    def process_exception(self, request, exception):
        """Log exceptions."""
        activity_logger.error(f"Exception occurred - {request.method} {request.path} - Error: {str(exception)}")
        return None 