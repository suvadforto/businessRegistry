#urls.py
# project/urls.py
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

    # Business report page (HTML + PDF)
    path('businesses/', views.businesses_report, name='business_list'),
    path('businesses/report/', views.businesses_report, name='businesses_report'),
    path('businesses/activity/', views.business_activity_report, name='business_activity_report'),
    #path("admin/owner-gender-stats/", views.owner_gender_stats, name="owner_gender_stats"),
    # API endpoints
    path('api/', include(router.urls)),
]

# ==========================
# Media files (development only)
# ==========================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)