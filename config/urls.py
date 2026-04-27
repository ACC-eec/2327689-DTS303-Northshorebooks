"""
URL configuration for northshore project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from accounts.views import ThrottledTokenObtainPairView
from catalogue import api

# API Router
api_router = DefaultRouter()
api_router.register(r'books', api.BookViewSet, basename='book')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_router.urls)),
    # JWT authentication endpoints
    path('api/auth/token/', ThrottledTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # OpenAPI schema + interactive docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('orders/', include('orders.urls')),
    path('accounts/', include('accounts.urls')),
    path('', include('catalogue.urls')),  # Home page and book routes
]

# Serve static files during development
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from config.staticfiles_handler import staticfiles_serve
    from django.urls import re_path

    # Use custom handler to ensure correct MIME types for CSS, JS, and SVG files
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', staticfiles_serve, name='static'),
    ]
    # Also add staticfiles_urlpatterns as fallback for other static files
    urlpatterns += staticfiles_urlpatterns()
    # Serve user-uploaded media (book covers) in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
