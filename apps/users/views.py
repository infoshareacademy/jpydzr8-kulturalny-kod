import datetime
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
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode, url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic.edit import FormView
from django.views.generic import UpdateView, DetailView, TemplateView
import json
from typing import cast

from .forms import CustomUserCreationForm, CustomUserChangeForm, UserProfileForm
from .models import UserProfile
from apps.booking.models import BookingItem

from kulturalny_kod.logger import get_logger
logger = get_logger(__name__)

from kulturalny_kod.mailer import notify_admin

# Create your views here.
class CustomLoginView(LoginView):
    template_name = 'users/user_login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        user = self.request.user if self.request.user.is_authenticated else "Anonymous"

        try:
            role = user.profile.role
        except Exception:
            role = "user"

        if role == "super_user":
            return reverse_lazy('users:super_user_dashboard')

        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={self.request.get_host()}):
            logger.info(f"Użytkownik {user} przekierowany do {next_url} po zalogowaniu.")
            return next_url

        logger.info(f"Użytkownik {user} zalogowany, przekierowany na stronę główną.")
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
        logger.info(f"Utworzono konto dla {user.email}. Wysłano mail aktywacyjny na domenę {current_site.domain}.")
        notify_admin(
            "Nowy użytkownik",
            f"Użytkownik {user.username}, e-mail: {user.email}"
        )
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
            logger.info(f"Konto użytkownika {user.email} zostało aktywowane.")
            # Optional: login user here
            return redirect('users:login')
        else:
            logger.warning(f"Nieudana próba aktywacji konta: uid={uidb64}, token={token}.")
            return render(request, 'activation_invalid.html')

class AccountActivationSentView(TemplateView):
    template_name = 'users/account_activation_sent.html'

class UserHomeView(LoginRequiredMixin, View):
    login_url = 'users:login'
    
    def get(self, request):
        request.session.pop("message", None)
        booking_items = BookingItem.objects.filter(booking__user=request.user).select_related('event')
        # bookings = request.user.bookings.select_related('event')
        booking_events = [
            {
                "date": b.event.date.isoformat(),
                "title": b.event.name,
                "city": b.event.city,
                "venue": b.event.venue,
            }
            for b in booking_items
        ]
        
        last_3_bookings = (
            booking_items
            .filter(event__date__lte=datetime.date.today())
            .order_by('-event__date')[:3]
        )
        
        nearest_3_bookings = (
            booking_items
            .filter(event__date__gte=datetime.date.today())
            .order_by('event__date')[:3]
        )

        return render(
            request,
            "users/user_home.html",
            {
                "last_3_bookings": last_3_bookings,
                "nearest_3_bookings": nearest_3_bookings,
                "booking_events": json.dumps(booking_events),
            }
        )

class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'users/user_edit.html'
    login_url = reverse_lazy('users:home')
    success_url = reverse_lazy('users:info')  # Redirect after saving
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add your custom context variables here
        
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        if self.request.method == 'POST':
            context['profile_form'] = UserProfileForm(self.request.POST, self.request.FILES, instance=profile)
        else :
            context['profile_form'] = UserProfileForm(instance=profile)


        return context

    # Ensure user can only edit their own profile
    def get_object(self, queryset=None) -> User:
        return cast(User, self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('users:info')
    
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
            elif 'profile_photo_url' in request.session:
                request.session.pop('profile_photo_url')
            logger.info(f"Użytkownik {request.user.username} zaktualizował profil.")
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
        logger.info(f"Użytkownik {request.user.username} wylogował się.")
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
