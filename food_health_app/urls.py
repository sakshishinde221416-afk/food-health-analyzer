"""
URL configuration for food_health_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from products.views import home_page_view, offline_page_view, service_worker_view, food_insights_view
from accounts.views import dashboard_view

urlpatterns = [
    path('', home_page_view, name='home'),
    path('sw.js', service_worker_view, name='service_worker'),
    path('offline/', offline_page_view, name='offline'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('insights/', food_insights_view, name='food_insights'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('health-analysis/', include('health_analysis.urls')),
]


