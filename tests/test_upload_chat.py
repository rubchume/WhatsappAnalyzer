from django.test import Client, TestCase
from rest_framework import status


class DashboardTests(TestCase):
    def test_upload_view_is_up_and_running(self):
        # When
        response = Client().get("/")
        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "<title>Upload Chat Export File</title>")
