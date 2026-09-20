from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = 'app/index.html'


class DashboardView(TemplateView):
    template_name = 'app/dashboard.html'


class TraderView(TemplateView):
    template_name = 'app/trader.html'


class AdminPanelView(TemplateView):
    template_name = 'app/admin_panel.html'


class LoginView(TemplateView):
    template_name = 'app/login.html'


class PersonalView(TemplateView):
    template_name = 'app/personal.html'



class TravellingView(TemplateView):
    template_name = 'app/travelling.html'

