import os
from pathlib import Path

from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from web_analyzer.forms import UploadChatForm


class UploadChatView(FormView):
    template_name = "upload_chat.html"
    form_class = UploadChatForm
    extra_context = {"title": "Upload Chat Export File"}
    success_url = reverse_lazy("chat_statistics")

    chat_exports_directory = "data"


    def form_valid(self, form):
        self.remove_old_chat_export()

        chat_export = form.files["chat_file"]
        self.request.session["chat_file_name"] = chat_export.name

        self.save_chat_export(chat_export)

        return super().form_valid(form)

    @classmethod
    def save_chat_export(cls, file):
        file_path = os.path.join(cls.chat_exports_directory, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

    def remove_old_chat_export(self):
        old_chat_export_file_name = self.request.session.get("chat_file_name", None)
        if old_chat_export_file_name:
            old_chat_export_file_path = Path(os.path.join(self.chat_exports_directory, old_chat_export_file_name))
            if old_chat_export_file_path.is_file():
                os.remove(old_chat_export_file_path)


class ChatStatisticsView(TemplateView):
    template_name = "chat_statistics.html"
    extra_context = {"title": "Chat Statistics"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chat_file_name"] = self.request.session["chat_file_name"]
        return context
