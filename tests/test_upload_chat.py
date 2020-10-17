import os
from pathlib import Path

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status


class DashboardTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        os.remove(os.path.join("data", "MyChat.txt"))
        os.remove(os.path.join("data", "MyChat2.txt"))

    def test_upload_view_is_up_and_running(self):
        # When
        response = Client().get("/")
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
        c.post("/", {"chat_file": uploaded_file})
        # Then
        self.assertEqual("MyChat.txt", c.session["chat_file_name"])

    def test_identify_chat_file_in_visualization_view(self):
        # Given
        filename = 'MyChat.txt'
        file = File(open('tests/helpers/ChatExample.txt', 'rb'))
        uploaded_file = SimpleUploadedFile(filename, file.read(), 'text/plain')
        c = Client()
        # When
        response = c.post("/", {"chat_file": uploaded_file})
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
        c.post("/", {"chat_file": uploaded_file})
        # Then
        self.assertTrue(Path("data/MyChat.txt").is_file())

    def test_delete_old_file_when_new_chat_associated_to_session(self):
        # Given
        file1 = File(open('tests/helpers/ChatExample.txt', 'rb'))
        file2 = File(open('tests/helpers/ChatExample.txt', 'rb'))
        uploaded_file1 = SimpleUploadedFile('MyChat.txt', file1.read(), 'text/plain')
        uploaded_file2 = SimpleUploadedFile('MyChat2.txt', file2.read(), 'text/plain')
        c = Client()
        c.post("/", {"chat_file": uploaded_file1})
        self.assertTrue(Path("data/MyChat.txt").is_file())
        # When
        c.post("/", {"chat_file": uploaded_file2})
        # Then
        self.assertEqual("MyChat2.txt", c.session["chat_file_name"])
        self.assertFalse(Path("data/MyChat.txt").is_file())
        self.assertTrue(Path("data/MyChat2.txt").is_file())
