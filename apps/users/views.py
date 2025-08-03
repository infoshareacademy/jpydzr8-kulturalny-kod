from django.contrib.auth.views import LoginView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm
from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.views import View
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.models import User

# Create your views here.
class CustomLoginView(LoginView):
    template_name = 'base_form.html'
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add your custom context variables here
        context['title'] = 'Please Log In'
        context['button_info'] = 'Log In'
        return context

class CustomRegisterView(FormView):
    form_class = CustomUserCreationForm
    template_name = 'base_form.html'
    success_url = reverse_lazy('account_activation_sent')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add your custom context variables here
        context['title'] = 'Please Register'
        context['button_info'] = 'Register'
        return context

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
            return redirect('login')
        else:
            return render(request, 'activation_invalid.html')
