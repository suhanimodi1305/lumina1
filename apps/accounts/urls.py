from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from . import views
from .forms import LuminaLoginForm, LuminaPasswordResetForm, LuminaSetPasswordForm

app_name = 'accounts'


class LoggedPasswordResetView(auth_views.PasswordResetView):
    """Extends Django's PasswordResetView to log every reset email in EmailLog."""

    def form_valid(self, form):
        email = form.cleaned_data.get('email', '')
        # Try to find the user for the log (silently skip if not found)
        try:
            user_obj = User.objects.filter(email__iexact=email).first()
        except Exception:
            user_obj = None

        response = super().form_valid(form)

        # Log the reset email after Django sends it
        views._log_email(
            user=user_obj,
            email_type='password_reset',
            recipient=email,
            subject='Lumina — Password Reset Request',
            body_preview='A password reset link was sent to this address.',
            ip=self.request.META.get('REMOTE_ADDR'),
        )
        return response


urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=LuminaLoginForm,
        redirect_authenticated_user=True,
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page=settings.LOGOUT_REDIRECT_URL
    ), name='logout'),

    # ── Password Reset (Forgot Password) ─────────────────────────────────────
    path('password-reset/',
         LoggedPasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             form_class=LuminaPasswordResetForm,
             email_template_name='accounts/emails/password_reset_email.html',
             subject_template_name='accounts/emails/password_reset_subject.txt',
             success_url='/accounts/password-reset/done/',
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html',
         ),
         name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             form_class=LuminaSetPasswordForm,
             success_url='/accounts/password-reset-complete/',
         ),
         name='password_reset_confirm'),

    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html',
         ),
         name='password_reset_complete'),

    # ── Session management ────────────────────────────────────────────────────
    path('session-status/', views.session_status, name='session_status'),
    path('session-ping/',   views.session_ping,   name='session_ping'),
]
