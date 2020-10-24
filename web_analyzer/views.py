import logging
import os
from pathlib import Path

from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from plotly.offline import plot

from src.chat_network import ChatNetwork
from web_analyzer.forms import UploadChatForm


logger = logging.getLogger("general")


CHAT_EXPORTS_DIRECTORY = "data"
SESSION_CHAT_FIELD = "chat_file_name"


class RedirectBasedOnRegisteredSessionMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.session.get(SESSION_CHAT_FIELD, None):
            return redirect(
                reverse_lazy(
                    "chat_statistics",
                )
            )
        else:
            return redirect(
                reverse_lazy(
                    "upload_chat",
                )
            )


class HomeView(RedirectBasedOnRegisteredSessionMixin, TemplateView):
    template_name = "upload_chat.html"


class UploadChatView(FormView):
    template_name = "upload_chat.html"
    form_class = UploadChatForm
    extra_context = {"title": "Upload Chat Export File"}
    success_url = reverse_lazy("chat_statistics")

    def form_valid(self, form):
        self.remove_old_chat_export()

        chat_export = form.files["chat_file"]
        self.request.session[SESSION_CHAT_FIELD] = chat_export.name

        self.save_chat_export(chat_export)
        logger.info(f"Chat {chat_export.name} uploaded")
        return super().form_valid(form)

    @classmethod
    def save_chat_export(cls, file):
        file_path = os.path.join(CHAT_EXPORTS_DIRECTORY, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

    def remove_old_chat_export(self):
        old_chat_export_file_name = self.request.session.get(SESSION_CHAT_FIELD, None)
        if old_chat_export_file_name:
            old_chat_export_file_path = Path(os.path.join(CHAT_EXPORTS_DIRECTORY, old_chat_export_file_name))
            if old_chat_export_file_path.is_file():
                os.remove(old_chat_export_file_path)


class ChatStatisticsView(TemplateView):
    template_name = "chat_statistics.html"
    extra_context = {"title": "Chat Statistics"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chat_export_file_name = self.request.session[SESSION_CHAT_FIELD]
        context["chat_file_name"] = chat_export_file_name
        context["graph"] = self.get_graphs(chat_export_file_name)
        return context

    @classmethod
    def get_graphs(cls, chat_export_file_name):
        chat_export_path = os.path.join(CHAT_EXPORTS_DIRECTORY, chat_export_file_name)
        chat_network = ChatNetwork(chat_export_path)
        fig = chat_network.draw()
        fig.update_layout(height=800)
        return plot(fig, output_type='div', include_plotlyjs=False)
