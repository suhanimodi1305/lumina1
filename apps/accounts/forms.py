"""
Custom authentication forms for Lumina
"""
from django import forms
from django.contrib.auth.forms import (
    UserCreationForm, AuthenticationForm,
    PasswordResetForm, SetPasswordForm,
)
from django.contrib.auth.models import User

# Common widget attrs — uses auth-input class (defined in login/signup templates)
_TEXT_ATTRS  = {'class': 'auth-input'}
_EMAIL_ATTRS = {'class': 'auth-input', 'placeholder': 'your@email.com'}
_PASS_ATTRS  = {'class': 'auth-input'}


class LuminaSignupForm(UserCreationForm):
    """Extended signup form with email field."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs=_EMAIL_ATTRS)
    )
    first_name = forms.CharField(
        max_length=30, required=False,
        widget=forms.TextInput(attrs={**_TEXT_ATTRS, 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=30, required=False,
        widget=forms.TextInput(attrs={**_TEXT_ATTRS, 'placeholder': 'Last name'})
    )

    referral_code = forms.CharField(
        max_length=12,
        required=False,
        label='Referral Code (optional)',
        widget=forms.TextInput(attrs={'placeholder': 'Enter referral code (optional)'}),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={**_TEXT_ATTRS, 'placeholder': 'Choose a username', 'autofocus': True})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({**_PASS_ATTRS, 'placeholder': 'Create a password'})
        self.fields['password2'].widget.attrs.update({**_PASS_ATTRS, 'placeholder': 'Confirm password'})


class LuminaLoginForm(AuthenticationForm):
    """Custom login form with styled fields."""
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={**_TEXT_ATTRS, 'placeholder': 'Username', 'autofocus': True})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={**_PASS_ATTRS, 'placeholder': 'Password'})
    )


class LuminaPasswordResetForm(PasswordResetForm):
    """Forgot-password form — styled email input."""
    email = forms.EmailField(
        label='Email address',
        max_length=254,
        widget=forms.EmailInput(attrs={
            **_EMAIL_ATTRS,
            'placeholder': 'Enter your account email',
            'autofocus': True,
        })
    )


class LuminaSetPasswordForm(SetPasswordForm):
    """Set-new-password form — styled inputs."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({**_PASS_ATTRS, 'placeholder': 'New password'})
        self.fields['new_password2'].widget.attrs.update({**_PASS_ATTRS, 'placeholder': 'Confirm new password'})
