from django import forms
from django.contrib.auth.forms import UserCreationForm
from core.models.user import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """
    Form kustom untuk registrasi, di-binding ke CustomUser model
    agar menghindari konflik Meta model.
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email')