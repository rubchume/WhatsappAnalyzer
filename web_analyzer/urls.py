from django.urls import path

from . import views

urlpatterns = [
    path('', views.UploadChatView.as_view(), name='upload_chat'),
]
