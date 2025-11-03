"""
URL configuration for kulturalny_kod project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from two_factor.urls import urlpatterns as tf_urls
from .views import home

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
]
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('account/', include(('apps.account.urls', 'account'), namespace='account')),
    path('events/', include('apps.events.urls')),
    path('', home, name='home'),
    path('booking/', include('apps.booking.urls', namespace='booking')),
    path('payments/', include('apps.payments.urls', namespace='payments')),
    path('venues/', include('apps.venues.urls', namespace='venues')),
    
    # mfa
    path('', include(tf_urls)),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
