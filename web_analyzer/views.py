import logging
import os
from pathlib import Path

from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView, TemplateView, RedirectView

from src.chat_network import ChatNetwork
from web_analyzer import dash_apps
from web_analyzer.forms import UploadChatForm


logger = logging.getLogger("general")


CHAT_EXPORTS_DIRECTORY = "data"
SESSION_CHAT_FIELD = "chat_file_name"
NODE_TRACES_FIELD = "node_traces"
EDGE_TRACES_FIELD = "edge_traces"


class HomeView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        def query_dict_to_string(query_dict):
            if not query_dict:
                return ""

            return "?" + "&".join([f"{key}={value}" for key, value in query_dict.items()])

        if self.request.session.get(SESSION_CHAT_FIELD, None):
            return reverse_lazy("chat_statistics")
        else:
            return reverse_lazy("upload_chat") + query_dict_to_string(self.request.GET)


class UploadChatView(FormView):
    template_name = "upload_chat.html"
    form_class = UploadChatForm
    extra_context = {"title": "Upload Chat Export File"}
    success_url = reverse_lazy("chat_statistics")

    def form_valid(self, form):
        self.remove_old_chat_export()
        self.remove_traces()

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

    def remove_traces(self):
        self.request.session[NODE_TRACES_FIELD] = None
        self.request.session[EDGE_TRACES_FIELD] = None


class RedirectIfChatNameIsMissingOrFileIsNotFoundMixin(object):
    def dispatch(self, request, *args, **kwargs):
        chat_export_file_name = self.request.session.get(SESSION_CHAT_FIELD, None)
        if not chat_export_file_name:
            return redirect(reverse("home"))

        chat_export_file_path = Path(CHAT_EXPORTS_DIRECTORY).joinpath(chat_export_file_name)
        if not chat_export_file_path.is_file():
            del self.request.session[SESSION_CHAT_FIELD]
            return redirect(reverse("home"))

        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception:
            chat_file_name = self.request.session[SESSION_CHAT_FIELD]
            chat_export_file_path = Path(CHAT_EXPORTS_DIRECTORY).joinpath(chat_file_name)
            os.remove(chat_export_file_path)

            del self.request.session[SESSION_CHAT_FIELD]

            return redirect(f"{reverse('home')}?error=true")


class ChatStatisticsView(RedirectIfChatNameIsMissingOrFileIsNotFoundMixin, TemplateView):
    template_name = "chat_statistics.html"
    extra_context = {"title": "Chat Statistics"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chat_export_file_name = self.request.session[SESSION_CHAT_FIELD]
        context["chat_file_name"] = chat_export_file_name
        return context

    def get(self, request, *args, **kwargs):
        self.update_graphs()
        return super().get(request, *args, **kwargs)

    def update_graphs(self):
        def get_chat_export_path():
            chat_export_file_name = self.request.session[SESSION_CHAT_FIELD]
            chat_export_path = os.path.join(CHAT_EXPORTS_DIRECTORY, chat_export_file_name)
            return chat_export_path

        def get_traces():
            node_traces = self.request.session.get(NODE_TRACES_FIELD, None)
            edge_traces = self.request.session.get(EDGE_TRACES_FIELD, None)
            return node_traces, edge_traces

        def traces_available():
            node_traces, edge_traces = get_traces()
            return node_traces and edge_traces

        def save_traces_to_session(node_traces, edge_traces):
            self.request.session[NODE_TRACES_FIELD] = node_traces
            self.request.session[EDGE_TRACES_FIELD] = edge_traces

        if not traces_available():
            chat_export_path = get_chat_export_path()
            chat_network = ChatNetwork(chat_export_path)
            fig, node_traces, edge_traces = chat_network.draw(return_traces=True)
            save_traces_to_session(node_traces, edge_traces)
            self.request.session["selected_nodes"] = []
        else:
            chat_network = ChatNetwork()
            node_traces, edge_traces = get_traces()
            fig = chat_network.draw(node_traces=node_traces, edge_traces=edge_traces)

        fig.update_layout(height=800)
        dash_apps.app.layout = dash_apps.create_app_layout(fig)
