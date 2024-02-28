
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AutocompleteSelect
from django.contrib.auth.admin import UserChangeForm, UserCreationForm
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.utils.translation import gettext_lazy as _

from base.models import ShiftSwapRequest, User, Shift, Role


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
    field_order = ['is_open', 'role']
    is_open = forms.BooleanField(initial=False, required=False)
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=AutocompleteSelect(Shift._meta.get_field('assigned_to'), admin.site,
                                  attrs={'id': 'assigned_to_input'}
                                  ),
        required=False,
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        widget=AutocompleteSelect(User._meta.get_field('role'), admin.site,
                                  attrs={'id': 'role_input'}
                                  ),
        required=False,
    )

    message = forms.CharField(max_length=512, required=False)

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

class ShiftSwapRequestForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['shift'].required = False

    class Meta:
        model = ShiftSwapRequest
        fields = ('shift', 'message',)

