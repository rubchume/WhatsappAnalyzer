from importlib import import_module
import os
from pathlib import Path
from unittest.mock import call, patch

from django.conf import settings
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
import plotly.graph_objects as go
from rest_framework import status

from src.chat_network import ChatNetwork


class WebTests(TestCase):
    def setUp(self):
        # https://stackoverflow.com/questions/4453764/how-do-i-modify-the-session-in-the-django-test-framework
        # http://code.djangoproject.com/ticket/10899
        settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()
        self.session = store
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key

    @classmethod
    def tearDownClass(cls):
        if Path(os.path.join("data", "MyChat.txt")).is_file():
            os.remove(os.path.join("data", "MyChat.txt"))

        if Path(os.path.join("data", "MyChat2.txt")).is_file():
            os.remove(os.path.join("data", "MyChat2.txt"))

    def add_data_to_session(self, data):
        session = self.session
        session.update(self.client.session)
        session.update(data)
        session.save()

    def test_upload_view_is_up_and_running(self):
        # When
        response = Client().get("/upload_chat/")
        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "<title>Upload Chat Export File</title>")

    def test_save_chat_file_name_in_session_information(self):
        # Given
        filename = 'MyChat.txt'
        file = File(open('tests/helpers/ChatExample.txt', 'rb'))
        uploaded_file = SimpleUploadedFile(filename, file.read(), 'text/plain')
        c = Client()
        # When
        c.post("/upload_chat/", {"chat_file": uploaded_file})
        # Then
        self.assertEqual("MyChat.txt", c.session["chat_file_name"])

    def test_identify_chat_file_in_visualization_view(self):
        # Given
        filename = 'MyChat.txt'
        file = File(open('tests/helpers/ChatExample.txt', 'rb'))
        uploaded_file = SimpleUploadedFile(filename, file.read(), 'text/plain')
        c = Client()
        # When
        response = c.post("/upload_chat/", {"chat_file": uploaded_file})
        # Then
        self.assertRedirects(
            response,
            reverse("chat_statistics"),
            status_code=302,
            target_status_code=200,
        )
        # When
        self.assertContains(c.get(response.url), "MyChat.txt")

    def test_upload_file(self):
        # Given
        filename = 'MyChat.txt'
        file = File(open('tests/helpers/ChatExample.txt', 'rb'))
        uploaded_file = SimpleUploadedFile(filename, file.read(), 'text/plain')
        c = Client()
        # When
        c.post("/upload_chat/", {"chat_file": uploaded_file})
        # Then
        self.assertTrue(Path("data/MyChat.txt").is_file())

    def test_delete_old_file_when_new_chat_associated_to_session(self):
        # Given
        file1 = File(open('tests/helpers/ChatExample.txt', 'rb'))
        file2 = File(open('tests/helpers/ChatExample.txt', 'rb'))
        uploaded_file1 = SimpleUploadedFile('MyChat.txt', file1.read(), 'text/plain')
        uploaded_file2 = SimpleUploadedFile('MyChat2.txt', file2.read(), 'text/plain')
        c = Client()
        c.post("/upload_chat/", {"chat_file": uploaded_file1})
        self.assertTrue(Path("data/MyChat.txt").is_file())
        # When
        c.post("/upload_chat/", {"chat_file": uploaded_file2})
        # Then
        self.assertEqual("MyChat2.txt", c.session["chat_file_name"])
        self.assertFalse(Path("data/MyChat.txt").is_file())
        self.assertTrue(Path("data/MyChat2.txt").is_file())

    def test_home_page_redirects_to_stats_page_if_session_file_is_not_empty(self):
        # Given
        file1 = File(open('tests/helpers/ChatExample.txt', 'rb'))
        uploaded_file = SimpleUploadedFile('MyChat.txt', file1.read(), 'text/plain')
        c = Client()
        c.post("/upload_chat/", {"chat_file": uploaded_file})
        # When
        response = c.get("/")
        # Then
        self.assertRedirects(
            response,
            reverse("chat_statistics"),
            status_code=302,
            target_status_code=200,
        )

    def test_home_page_redirects_to_upload_page_if_session_file_is_empty(self):
        # When
        response = Client().get("/")
        # Then
        self.assertRedirects(
            response,
            reverse("upload_chat"),
            status_code=302,
            target_status_code=200,
        )

    def test_chat_statistics_page_redirects_to_home_page_and_then_to_upload_page_if_chat_export_file_is_missing(self):
        # Given
        session = self.session
        session["chat_file_name"] = "example.txt"
        session.save()
        expected_redirections = [(reverse("home"), 302), (reverse('upload_chat'), 302)]
        # When
        response = self.client.get("/stats/", follow=True)
        # Then
        self.assertEqual(expected_redirections, response.redirect_chain)

    def test_chat_statistics_page_redirects_to_home_page_and_then_to_upload_page_if_chat_file_name_is_missing(self):
        # Given
        expected_redirections = [(reverse("home"), 302), (reverse('upload_chat'), 302)]
        # When
        response = Client().get("/stats/", follow=True)
        # Then
        self.assertEqual(expected_redirections, response.redirect_chain)

    def test_stats_page_redirects_to_home_and_then_upload_page_and_remove_file_if_error_in_decoding(self):
        # Given
        file1 = File(open('tests/helpers/ChatExampleWrong.PNG', 'rb'))
        uploaded_file = SimpleUploadedFile('MyChat.txt', file1.read(), 'text/plain')
        expected_redirections = [
            (reverse("home") + "?error=true", 302),
            (reverse('upload_chat') + "?error=true", 302)
        ]
        self.client.post("/upload_chat/", {"chat_file": uploaded_file})
        # When
        response = self.client.get("/stats/", follow=True)
        # Then
        self.assertEqual(expected_redirections, response.redirect_chain)
        self.assertIsNone(self.client.session.get("chat_file_name", None))
        self.assertContains(response, "Something went wrong. Try again")

    @patch.object(
        ChatNetwork,
        "draw",
        return_value=(go.Figure(), "node_traces", "edge_traces"),
        autospec=True
    )
    def test_calculate_traces_if_they_are_not_saved_in_session_and_save_them(self, draw_mock):
        # Given
        file1 = File(open('tests/helpers/ChatExample.txt', 'rb'))
        uploaded_file = SimpleUploadedFile('MyChat.txt', file1.read(), 'text/plain')
        c = Client()
        # When
        c.post("/upload_chat/", {"chat_file": uploaded_file}, follow=True)
        # Then
        draw_mock.assert_called_once_with(
            draw_mock.call_args[0][0], return_traces=True
        )
        self.assertEqual("node_traces", c.session["node_traces"])
        self.assertEqual("edge_traces", c.session["edge_traces"])

    @patch.object(
        ChatNetwork,
        "draw",
        return_value=go.Figure(),
        autospec=True
    )
    def test_use_traces_if_they_are_saved_in_session(self, draw_mock):
        # Given
        file1 = File(open('tests/helpers/ChatExample.txt', 'rb'))
        uploaded_file = SimpleUploadedFile('MyChat.txt', file1.read(), 'text/plain')
        self.client.post("/upload_chat/", {"chat_file": uploaded_file}, follow=False)

        self.add_data_to_session({
            "node_traces": "my_node_traces",
            "edge_traces": "my_edge_traces",
        })
        # When
        self.client.get("/stats/")
        # Then
        draw_mock.assert_called_once_with(
            draw_mock.call_args[0][0], node_traces="my_node_traces", edge_traces="my_edge_traces"
        )

    @patch.object(
        ChatNetwork,
        "draw",
        side_effect=[(go.Figure(), "node_traces", "edge_traces"), go.Figure()],
        autospec=True
    )
    def test_calculate_traces_and_then_use_them_next_time_you_visit_the_page(self, draw_mock):
        # Given
        file1 = File(open('tests/helpers/ChatExample.txt', 'rb'))
        uploaded_file = SimpleUploadedFile('MyChat.txt', file1.read(), 'text/plain')
        c = Client()
        c.post("/upload_chat/", {"chat_file": uploaded_file}, follow=True)
        # When
        c.get("/stats/")
        # Then
        draw_mock.assert_has_calls([
            call(draw_mock.call_args_list[0][0][0], return_traces=True),
            call(draw_mock.call_args_list[1][0][0], node_traces="node_traces", edge_traces="edge_traces")
        ])
        self.assertEqual("node_traces", c.session["node_traces"])
        self.assertEqual("edge_traces", c.session["edge_traces"])

    @patch.object(
        ChatNetwork,
        "draw",
        return_value=(go.Figure(), "node_traces", "edge_traces"),
        autospec=True
    )
    def test_delete_traces_from_session_when_new_chat_is_uploaded(self, draw_mock):
        # Given
        self.add_data_to_session({
            "node_traces": "node_traces",
            "edge_traces": "edge_traces",
        })

        file1 = File(open('tests/helpers/ChatExample.txt', 'rb'))
        uploaded_file = SimpleUploadedFile('MyChat.txt', file1.read(), 'text/plain')
        file1.close()
        self.client.post("/upload_chat/", {"chat_file": uploaded_file}, follow=False)
        # When
        file1 = File(open('tests/helpers/ChatExample.txt', 'rb'))
        uploaded_file = SimpleUploadedFile('MyChat.txt', file1.read(), 'text/plain')
        file1.close()
        self.client.post("/upload_chat/", {"chat_file": uploaded_file}, follow=True)
        # Then
        draw_mock.assert_called_once_with(
            draw_mock.call_args[0][0], return_traces=True
        )
        self.assertEqual("node_traces", self.client.session["node_traces"])
        self.assertEqual("edge_traces", self.client.session["edge_traces"])
