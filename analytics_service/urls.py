from django.urls import path
from . import views

urlpatterns = [
    # Lab endpoints
    path('labs/', views.get_all_labs, name='get_all_labs'),
    path('lab/<int:lab_id>/', views.get_lab_by_id, name='get_lab_by_id'),
    
    # Student endpoints
    path('students/', views.get_all_students, name='get_all_students'),
    path('student/<str:student_id>/', views.get_student_details, name='get_student_details'),
    path('student/<str:student_id>/performance/', views.get_student_performance_summary, name='get_student_performance_summary'),  # Performance summary endpoint
    path('performance/analysis/', views.analyze_student_performance, name='analyze_student_performance'),
    path('performance/by-lab/', views.get_student_performance_by_lab, name='get_student_performance_by_lab'),
    
    # Summarized performance endpoints
    path('performance/lab/<str:lab_name>/', views.get_summarized_performance_by_lab, name='get_summarized_performance_by_lab'),
    path('performance/section/<str:section>/', views.get_summarized_performance_by_section, name='get_summarized_performance_by_section'),
    path('performance/semester/<str:semester>/', views.get_summarized_performance_by_semester, name='get_summarized_performance_by_semester'),
    
    # Performance analysis endpoints
    path('lab/<str:lab_name>/section/<str:section>/', views.analyze_lab_section, name='analyze_lab_section'),
    path('lab/<str:lab_name>/', views.analyze_lab, name='analyze_lab'),
    path('semester/<str:semester>/', views.analyze_semester, name='analyze_semester'),
    path('lab/<str:lab_name>/semester/<str:semester>/', views.analyze_lab_semester, name='analyze_lab_semester'),
] 