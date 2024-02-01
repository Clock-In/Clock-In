
from django import forms
from django.contrib.auth.admin import UserChangeForm, UserCreationForm

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

