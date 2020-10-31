import io
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


class RedirectToHomeIfErrorDecodingMixin(object):
    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except DecodingError:
            del self.request.session[SESSION_CHAT_FIELD]
            return redirect(f"{reverse('home')}?decodingerror=true")


class UploadChatView(RedirectToHomeIfErrorDecodingMixin, FormView):
    template_name = "upload_chat.html"
    form_class = UploadChatForm
    extra_context = {"title": "Upload Chat Export File"}
    success_url = reverse_lazy("chat_statistics")

    def form_valid(self, form):
        self.remove_old_chat_export()
        self.remove_traces()

        chat_export = form.files["chat_file"]
        self.request.session[SESSION_CHAT_FIELD] = chat_export.name

        try:
            chat_text = chat_export.read().decode("utf-8")
            chat_file_stream = io.StringIO(chat_text)
            _, node_traces, edge_traces = ChatNetwork(whatsapp_export_file=chat_file_stream).draw(return_traces=True)
        except Exception:
            raise DecodingError

        self.request.session[NODE_TRACES_FIELD] = node_traces
        self.request.session[EDGE_TRACES_FIELD] = edge_traces
        self.request.session["selected_nodes"] = []

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


class RedirectIfChatNameOrTracesAreMissingMixin(object):
    def dispatch(self, request, *args, **kwargs):
        chat_export_file_name = self.request.session.get(SESSION_CHAT_FIELD, None)
        if not chat_export_file_name:
            return redirect(reverse("home"))

        node_traces = self.request.session.get(NODE_TRACES_FIELD, None)
        edge_traces = self.request.session.get(EDGE_TRACES_FIELD, None)
        if not (node_traces and edge_traces):
            del self.request.session[SESSION_CHAT_FIELD]
            return redirect(reverse("home"))

        return super().dispatch(request, *args, **kwargs)


class ChatStatisticsView(RedirectIfChatNameOrTracesAreMissingMixin, TemplateView):
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
        def get_traces():
            node_traces = self.request.session.get(NODE_TRACES_FIELD, None)
            edge_traces = self.request.session.get(EDGE_TRACES_FIELD, None)
            return node_traces, edge_traces

        chat_network = ChatNetwork()
        node_traces, edge_traces = get_traces()
        fig = chat_network.draw(node_traces=node_traces, edge_traces=edge_traces)

        fig.update_layout(height=800)
        dash_apps.app.layout = dash_apps.create_app_layout(fig)


class DecodingError(RuntimeError):
    pass
