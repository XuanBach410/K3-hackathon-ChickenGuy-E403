from django.contrib import admin
from django.urls import path
from evaluator import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/topics/', views.get_topics),
    path('api/profiles/', views.get_mock_profiles),
    path('api/evaluate/preliminary/', views.evaluate_preliminary),
    path('api/evaluate/deep-quiz/', views.generate_deep_quiz),
    path('api/evaluate/final/', views.evaluate_final),
]
