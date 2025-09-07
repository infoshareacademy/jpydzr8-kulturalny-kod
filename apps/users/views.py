from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordChangeView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from django.views.generic.edit import FormView
from django.views.generic import UpdateView, DetailView, TemplateView
from typing import cast

from .forms import CustomUserCreationForm, CustomUserChangeForm, UserProfileForm
from .models import UserProfile

# Create your views here.
class CustomLoginView(LoginView):
    template_name = 'users/user_login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('users:home')
     
    def form_valid(self, form):
        """Called when the login form is valid (successful login)."""
        response = super().form_valid(form)

        # Ensure profile exists
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)

        if profile.photo:
            self.request.session['profile_photo_url'] = profile.photo.url

        return response

class CustomRegisterView(FormView):
    form_class = CustomUserCreationForm
    template_name = 'users/user_registration.html'
    success_url = reverse_lazy('users:account_activation_sent')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        current_site = get_current_site(self.request)
        mail_subject = 'Activate your account'
        message = render_to_string('users/activation_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })

        email = EmailMessage(mail_subject, message, to=[user.email])
        email.send()

        return super().form_valid(form)

class ActivateAccount(View):
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            # Optional: login user here
            return redirect('users:login')
        else:
            return render(request, 'activation_invalid.html')

class AccountActivationSentView(TemplateView):
    template_name = 'users/account_activation_sent.html'

class UserHomeView(LoginRequiredMixin, View):
    login_url = 'users:login'
    
    def get(self, request):
        request.session.pop("message", None)
        return render(request, "users/user_home.html")

class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'users/user_edit.html'
    login_url = reverse_lazy('users:home')
    success_url = reverse_lazy('users:home')  # Redirect after saving
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add your custom context variables here
        
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        if self.request.method == 'POST':
            context['profile_form'] = UserProfileForm(self.request.POST, self.request.FILES, instance=profile)
        else:
            context['profile_form'] = UserProfileForm(instance=profile)

        
        return context

    # Ensure user can only edit their own profile
    def get_object(self, queryset=None) -> User:
        return cast(User, self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('users:home')
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid() and profile_form.is_valid():
            user = form.save(commit=False)
            user.save()
            profile_form.save()

            if profile.photo:
                request.session['profile_photo_url'] = profile.photo.url
            else:
                request.session.pop('profile_photo_url')

            return redirect(self.get_success_url())
        return self.form_invalid(form)
    
class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/user_info.html'
    login_url = reverse_lazy('users:home')
    
    def get_object(self, queryset=None) -> User:
        return cast(User, self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add your custom context variables here
        
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        context['profile'] = profile
        return context
    
class CustomLogoutView(LoginRequiredMixin, LogoutView):
    next_page = '/'  # or reverse_lazy('users:home')

    def dispatch(self, request, *args, **kwargs):
        # Remove profile data from session
        request.session.pop('profile_photo_url', None)
        return super().dispatch(request, *args, **kwargs)

class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/user_reset_password.html'
    email_template_name = 'users/user_reset_password_email.html'
    success_url = reverse_lazy('users:password_reset_sent')
    
class ResetPasswordSentView(TemplateView):
    template_name = 'users/user_reset_password_done.html'

class CustomPasswordChangeView(PasswordChangeView):
    template_name = "users/user_change_password.html"
    success_url = reverse_lazy('users:home')
