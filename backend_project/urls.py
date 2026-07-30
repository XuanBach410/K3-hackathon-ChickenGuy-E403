from django.contrib import admin
from django.urls import path
from evaluator import views

urlpatterns = [
    path('', views.serve_index),
    path('admin/', admin.site.urls),
    path('api/topics/', views.get_topics),
    path('api/profiles/', views.get_mock_profiles),
    path('api/agent/tools/', views.get_registered_agent_tools),
    path('api/health/', views.health),
    path('api/evaluate/preliminary/', views.evaluate_preliminary),
    path('api/evaluate/deep-quiz/', views.generate_deep_quiz),
    path('api/evaluate/verify-skills/', views.verify_declared_skills),
    path('api/evaluate/final/', views.evaluate_final),
    path('api/evaluate/what-if/', views.evaluate_what_if),
]
