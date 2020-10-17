from django import forms


class UploadChatForm(forms.Form):
    chat_file = forms.FileField(label="Chat Export File")
