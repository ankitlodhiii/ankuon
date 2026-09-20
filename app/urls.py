from django.contrib import admin
from django.urls import path, include

from app.views import (
    IndexView,
    DashboardView,
    AdminPanelView,
    LoginView,
    PersonalView,
    TraderView,
    TravellingView,
)


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', IndexView.as_view(), name='index'),

    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    path('trader/', TraderView.as_view(), name='trader'),

    path('login/', LoginView.as_view(), name='login'),

    path('admin-panel/', AdminPanelView.as_view(), name='admin_panel'),

    path('personal/', PersonalView.as_view(), name='personal'),

    path('travelling/', TravellingView.as_view(), name='travelling'),

    path('api/', include('app.api.urls')),
]
