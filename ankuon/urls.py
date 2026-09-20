from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from app.views import IndexView


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', IndexView.as_view(), name='index'),

    path(
        'dashboard/',
        TemplateView.as_view(template_name='app/dashboard.html'),
        name='dashboard'
    ),

    path(
        'trader/',
        TemplateView.as_view(template_name='app/trader.html'),
        name='trader'
    ),

    path(
        'login/',
        TemplateView.as_view(template_name='app/login.html'),
        name='login'
    ),

    path(
        'admin-panel/',
        TemplateView.as_view(template_name='app/admin_panel.html'),
        name='admin_panel'
    ),

    path(
        'personal/',
        TemplateView.as_view(template_name='app/personal.html'),
        name='personal'
    ),

    path(
        'travelling/',
        TemplateView.as_view(template_name='app/travelling.html'),
        name='travelling'
    ),

    path('api/', include('app.api.urls')),
]
