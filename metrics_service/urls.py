from django.urls import path
from . import views

urlpatterns = [
    # Dashboard and summary endpoints
    path('dashboard/', views.system_health_dashboard, name='system_health_dashboard'),
    path('summary/', views.get_metrics_summary, name='metrics_summary'),
    
    # Detailed analysis endpoints
    path('costs/', views.get_cost_analysis, name='cost_analysis'),
    path('costs', views.get_cost_analysis, name='cost_analysis_alias'),  # Alias without trailing slash
    path('performance/', views.get_performance_summary, name='performance_summary'),
    
    # Management endpoints
    path('update-daily/', views.update_daily_metrics, name='update_daily_metrics'),
    path('requests/', views.get_request_metrics, name='request_metrics'),
    path('tokens/', views.get_token_usage, name='token_usage'),
    path('cache/', views.get_cache_status, name='cache_status'),
] 