
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
        
class ExtendedCustomUserChangeForm(UserChangeForm):
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')
    
    first_name = forms.CharField(max_length=100,
                               required=True,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'first_name_input'}))
    last_name = forms.CharField(max_length=100,
                               required=True,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'last_name_input'}))
    email = forms.EmailField(required=True,
                             widget=forms.EmailInput(attrs={'class': 'form-control', 'id': 'email_input'}))
        
class ShiftCreationForm(forms.ModelForm):

    class Meta:
        model = Shift
        fields = ('assigned_to', 'start_at', 'end_at', 'wage_multiplier')

class ShiftChangeForm(forms.ModelForm):

    class Meta:
        model = Shift
        fields = ('assigned_to', 'start_at', 'end_at', 'wage_multiplier')

