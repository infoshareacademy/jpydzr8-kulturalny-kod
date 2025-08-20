from django.contrib import admin
from django.urls import path, reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth.views import LogoutView, PasswordResetView, PasswordChangeView
from .views import \
    CustomLoginView, CustomRegisterView, ActivateAccount, UserHomeView, \
    UserUpdateView, UserDetailView, AccountActivationSentView, CustomLogoutView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', CustomRegisterView.as_view(), name='register'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('activate/<uidb64>/<token>/', ActivateAccount.as_view(), name='activate'),
    path('account-activation-sent/', AccountActivationSentView.as_view(), name='account_activation_sent'),
    path('home/', UserHomeView.as_view(), name='home'),
    path('edit/', UserUpdateView.as_view(), name='edit'),
    path(
        'edit/change_password/', 
        PasswordChangeView.as_view(
            template_name='base_form.html',
            success_url=reverse_lazy('users:home'),
            extra_context={
                'title': 'Zmień hasło',
                'button_info': 'Zmień hasło'
            }
        ), 
        name='password_change'
    ),
    path('info/', UserDetailView.as_view(), name='info'),
    path('password_reset/', PasswordResetView.as_view(
        template_name='base_form.html',
        success_url='home'
    ), name='password_reset')
]
