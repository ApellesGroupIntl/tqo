"""
URL configuration for tqo project.

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
# from django.contrib import admin
# from django.urls import path
#
# urlpatterns = [
#     path('admin/', admin.site.urls),
# ]

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from users import views as user_views
from django.conf.urls.static import static
from django.conf import settings

from django.urls import path
from users import views
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from users import views as user_views


from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from users import views as user_views
from django.conf.urls.static import static
from django.conf import settings
from django.shortcuts import render
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),

    # Custom login/logout/register views
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', user_views.custom_logout_view, name='logout'),
    path('accounts/logged_out/', lambda request: render(request, 'registration/logged_out.html'), name='logged_out'),
    path('register/', user_views.register, name='register'),
    path('dashboard/', user_views.dashboard, name='dashboard'),

    # DRF API paths
    path('api/users/', include(('users.urls', 'users'), namespace='users-api')),
    # path('api/events/', include(('events.api_urls', 'events'), namespace='events-api')),
    # path('api/payments/', include(('payments.api_urls', 'payments'), namespace='payments-api')),

    # App routes
    path('', include(('events.urls', 'events'), namespace='events')),
    path('payments/', include(('payments.urls', 'payments'), namespace='payments')),
    path('users/', include(('users.urls', 'users'), namespace='users')),

    # Django auth (if needed)
    path('accounts/', include('django.contrib.auth.urls')),


]

# Media files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




#
# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('api/users/', include('users.urls')),
#     path('api/events/', include('events.urls')),
#     path('api/payments/', include('payments.urls')),
#     path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
#     path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
#     path('register/', user_views.register, name='register'),
#     path('dashboard/', user_views.dashboard, name='dashboard'),
#     path('', include(('events.urls', 'events'), namespace='events')),
#     path('payments/', include(('payments.urls', 'payments'), namespace='payments')),
#     path('accounts/', include('django.contrib.auth.urls')),
#     path('', include('users.urls')),
#     path('events/', include('events.urls', namespace='event')),
#     path('accounts/logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
#     path('accounts/logout/', views.custom_logout_view, name='logout'),
#     path('accounts/logged_out/', lambda request: render(request, 'registration/logged_out.html'), name='logged_out'),
#     ]
#
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
