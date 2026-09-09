from django.urls import path
from . import views

urlpatterns = [
    path('gemini-test/', views.gemini_test_view, name='gemini_test'),
    path('product/<str:barcode>/', views.product_health_analysis_view, name='product_health_analysis'),
    path('compare/<str:barcode_a>/<str:barcode_b>/', views.product_comparison_analysis_view, name='compare_analysis'),
    path('ai-insights/', views.generate_ai_insights_view, name='generate_ai_insights'),
]
