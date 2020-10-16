from django.views.generic import TemplateView


class UploadChatView(TemplateView):
    template_name = "base.html"
    extra_context = {"title": "Upload Chat Export File"}
