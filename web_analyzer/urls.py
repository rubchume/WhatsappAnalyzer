from django.urls import path

from . import views

urlpatterns = [
    path('', views.UploadChatView.as_view(), name='upload_chat'),
    path('stats/', views.ChatStatisticsView.as_view(), name='chat_statistics'),
]
