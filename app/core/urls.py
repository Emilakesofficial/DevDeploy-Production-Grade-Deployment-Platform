from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.views.generic import TemplateView
from rest_framework.permissions import AllowAny

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='api_docs.html'), name='api-home'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(
            url_name='schema',
            permission_classes=[AllowAny]
        ),
        name='swagger-ui'
    ),

    # ReDoc — explicitly allow any
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(
            url_name='schema',
            permission_classes=[AllowAny]
        ),
        name='redoc'
    ),
    path('api/auth/', include('accounts.urls')),
]

