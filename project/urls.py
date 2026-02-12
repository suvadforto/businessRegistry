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
from registry import views
#from django.contrib import admin
#from django.urls import path

#urlpatterns = [
#    path('admin/', admin.site.urls),
#]


from django.conf import settings
from django.conf.urls.static import static


from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from registry.api import BusinessViewSet

router = routers.DefaultRouter()
router.register(r'businesses', BusinessViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('businesses/', views.business_list, name='business_list'),
    path('api/', include(router.urls)),  # <-- API endpoint
]
    
    
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
