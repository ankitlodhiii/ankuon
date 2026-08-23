from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from app.views import IndexView, DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', IndexView.as_view(), name='index'),

    # Investor App = your dashboard.html
    path('dashboard/', TemplateView.as_view(template_name='app/dashboard.html'), name='dashboard'),

    # just testing
    path('login/', TemplateView.as_view(template_name='app/login.html'), name='login'),

    # Admin Panel
    path('admin-panel/', TemplateView.as_view(template_name='app/admin_panel.html'), name='admin_panel'),

    path('api/', include('app.api.urls')),
]
