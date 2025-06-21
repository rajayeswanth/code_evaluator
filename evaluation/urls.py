from django.urls import path
from . import views

urlpatterns = [
    # Simple API endpoints
    path('create-rubric/', views.create_rubric, name='create_rubric'),
    path('get-rubric-id/', views.get_rubric_id, name='get_rubric_id'),
    path('evaluate/', views.evaluate_submission, name='evaluate_submission'),
    path('rubrics/', views.get_rubrics, name='get_rubrics'),
    path('health/', views.health_check, name='health_check'),
    path('evaluations/', views.get_all_evaluations, name='get_all_evaluations'),
    path('evaluations/<int:evaluation_id>/', views.get_evaluation_by_id, name='get_evaluation_by_id'),
    path('evaluations/<int:evaluation_id>/llm-metrics/', views.get_llm_metrics_by_evaluation, name='get_llm_metrics_by_evaluation'),
] 