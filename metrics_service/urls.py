from django.urls import path
from . import views

urlpatterns = [
    # Dashboard and summary endpoints
    path('dashboard/', views.system_health_dashboard, name='system_health_dashboard'),
    path('summary/', views.metrics_summary, name='metrics_summary'),
    
    # Detailed analysis endpoints
    path('costs/', views.cost_analysis, name='costs'),  # Alias for backward compatibility
    path('cost-analysis/', views.cost_analysis, name='cost_analysis'),
    path('performance/', views.performance_trends, name='performance'),  # Shorter alias
    path('performance-trends/', views.performance_trends, name='performance_trends'),
    
    # Management endpoints
    path('update-daily/', views.update_daily_metrics, name='update_daily_metrics'),
    path('request-metrics/', views.get_request_metrics, name='get_request_metrics'),
] 