from django.contrib import admin
from django.urls import path, include
from app.views import IndexView, DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', IndexView.as_view(), name='index'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api/', include('app.api.urls')),  # For API routes
]
