from django.views.generic import TemplateView


class HelpView(TemplateView):
    """Page d'aide et documentation"""
    template_name = 'help.html'




