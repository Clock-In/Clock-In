
from django import forms
from django.contrib.auth.admin import UserChangeForm, UserCreationForm
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.utils.translation import gettext_lazy as _

from base.models import User, Shift


class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('email',)

class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = User
        fields = ('email',)

class ShiftCreationForm(forms.ModelForm):

    class Meta:
        model = Shift
        fields = ('assigned_to', 'start_at', 'end_at', 'wage_multiplier')

class ShiftChangeForm(forms.ModelForm):

    class Meta:
        model = Shift
        fields = ('assigned_to', 'start_at', 'end_at', 'wage_multiplier')

class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={"autofocus": True, "class": "inputs", "placeholder": "email address", "type": "email"}))
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "class": "inputs", "placeholder": "password"}),
    )

