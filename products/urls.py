from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.barcode_search_page_view, name='barcode_search'),
    path('compare/', views.compare_products_view, name='compare_products'),
    path('saved/', views.saved_products_page_view, name='saved_products'),
    path('saved/toggle/<str:barcode>/', views.toggle_favorite_view, name='toggle_favorite'),
    path('history/', views.scan_history_view, name='scan_history'),
    path('history/delete/<int:item_id>/', views.delete_scan_history_item_view, name='delete_scan_history_item'),
    path('history/clear/', views.clear_scan_history_view, name='clear_scan_history'),
    path('lookup/<str:barcode>/', views.barcode_lookup_view, name='barcode_lookup'),
]

