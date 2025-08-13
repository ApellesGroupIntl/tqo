from django.urls import path
from .views import RegisterView, custom_logout_view
from users import views as user_views

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('logout/', custom_logout_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', user_views.register, name='register'),

]




# from django.urls import path
# from .views import RegisterView
# from django.contrib.auth import views as auth_views
#
# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
# )
#
# app_name = 'users'
#
#
# urlpatterns = [
#     path('register/', RegisterView.as_view(), name='register'),
#     path('login/', TokenObtainPairView.as_view(), name='login'),
#     path('accounts/logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
#     path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
# ]
