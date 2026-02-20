"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers

from registry import views
from registry.api import BusinessViewSet


# ==========================
# DRF Router
# ==========================

router = routers.DefaultRouter()
router.register(r'businesses', BusinessViewSet)


# ==========================
# URL Patterns
# ==========================

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),

    # HTML business list
    path('businesses/', views.business_list, name='business_list'),

    # ✅ PDF report
    path('businesses/report/', views.businesses_report, name='businesses_report'),

    # API endpoints
    path('api/', include(router.urls)),
]


# ==========================
# Media files (development only)
# ==========================

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
