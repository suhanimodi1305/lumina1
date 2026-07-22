"""
Custom authentication forms for Lumina
"""
from django import forms
from django.contrib.auth.forms import (
    UserCreationForm, AuthenticationForm,
    PasswordResetForm, SetPasswordForm,
)
from django.contrib.auth.models import User
from .models import SavedAddress

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
    """Allow users to sign in with either username or account email."""
    username = forms.CharField(
        label='Username or email',
        widget=forms.TextInput(attrs={**_TEXT_ATTRS, 'placeholder': 'Username or email', 'autofocus': True})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={**_PASS_ATTRS, 'placeholder': 'Password'})
    )

    def clean_username(self):
        """Normalize typed credentials before Django authenticates them."""
        identifier = self.cleaned_data['username'].strip()
        user = User.objects.filter(email__iexact=identifier).order_by('pk').first()
        if not user:
            user = User.objects.filter(username__iexact=identifier).order_by('pk').first()
        if user:
            return user.get_username()
        return identifier


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


# ── Edit Profile ──────────────────────────────────────────────────────────────

class EditProfileForm(forms.Form):
    """Form to update basic user info (name, email, phone, bio)."""
    first_name = forms.CharField(
        max_length=30, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=30, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'})
    )
    phone = forms.CharField(
        max_length=15, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 9876543210'})
    )
    bio = forms.CharField(
        max_length=300, required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'A short bio…'})
    )
    age_group = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Select age group'),
            ('under_18',  'Under 18'),
            ('18_24',     '18 – 24'),
            ('25_34',     '25 – 34'),
            ('35_44',     '35 – 44'),
            ('45_54',     '45 – 54'),
            ('55_plus',   '55+'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    skin_goal = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Select primary skin goal'),
            ('acne',        'Clear acne & breakouts'),
            ('brightening', 'Brightening & glow'),
            ('anti_aging',  'Anti-aging & firming'),
            ('hydration',   'Deep hydration'),
            ('sensitive',   'Calm sensitive skin'),
            ('pigmentation','Fade pigmentation & dark spots'),
            ('general',     'General skincare'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


# ── Saved Address ─────────────────────────────────────────────────────────────

class SavedAddressForm(forms.ModelForm):
    """Form for adding / editing a saved address."""
    class Meta:
        model = SavedAddress
        fields = ['label', 'full_name', 'phone', 'address_line1',
                  'address_line2', 'city', 'state', 'pincode', 'is_default']
        widgets = {
            'label':         forms.Select(attrs={'class': 'form-select'}),
            'full_name':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'phone':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'House / flat / street'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Area / landmark (optional)'}),
            'city':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'pincode':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PIN code'}),
            'is_default':    forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
