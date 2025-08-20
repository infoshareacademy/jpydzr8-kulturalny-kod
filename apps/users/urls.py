from django.contrib import admin
from django.urls import path, reverse_lazy
from django.contrib.auth.views import PasswordResetConfirmView, PasswordChangeView
from .views import \
    CustomLoginView, CustomRegisterView, ActivateAccount, UserHomeView, \
    UserUpdateView, UserDetailView, AccountActivationSentView, CustomLogoutView, \
    CustomPasswordResetView, ResetPasswordSentView

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
        ), 
        name='password_change'
    ),
    path('info/', UserDetailView.as_view(), name='info'),
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', ResetPasswordSentView.as_view(), name='password_reset_sent'),
    path('reset/<uidb64>/<token>/', 
        PasswordResetConfirmView.as_view(
            template_name='users/user_reset_password_confirm.html',
            success_url=reverse_lazy('users:home'),
        ), 
         name='password_reset_confirm'),
]
