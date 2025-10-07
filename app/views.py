from django.views.generic import TemplateView

class IndexView(TemplateView):
    template_name = 'app/index.html'  # Updated to use app/index.html

class DashboardView(TemplateView):
    template_name = 'app/dashboard.html'  # Updated to use app/dashboard.html
