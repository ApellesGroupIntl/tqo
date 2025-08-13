from django.contrib.auth import get_user_model
from rest_framework import generics
from .serializers import RegisterSerializer
from rest_framework.permissions import AllowAny
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from payments.models import Payment
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
User = get_user_model()
# users/views.py
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('dashboard')
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords don't match.")
            return redirect('register')

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')

        user = User.objects.create_user(
            username=username,
            password=password1
        )
        login(request, user)  # Automatically log in after registration
        messages.success(request, "Registration successful!")
        return redirect('dashboard')

    return render(request, 'users/register.html')


# def register(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         if User.objects.filter(username__iexact=username).exists():
#             messages.error(request, "Username already exists.")
#             return redirect('register')
#
#         password = request.POST.get('password')
#         user = User.objects.create_user(username=username, password=password)
#         messages.success(request, "Registration successful.")
#         return redirect('login')
#
#     return render(request, 'users/register.html')

@login_required
def dashboard(request):
    tickets = Payment.objects.filter(user=request.user, status='success')
    return render(request, 'users/dashboard.html', {'tickets': tickets})

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

def custom_logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('logged_out')
    return render(request, 'registration/logout_confirm.html')



# from rest_framework import generics
# from .models import User
# from .serializers import RegisterSerializer
# from rest_framework.permissions import AllowAny
# from django.shortcuts import render
# from django.shortcuts import render, redirect
# from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.decorators import login_required
# from payments.models import Payment
# from django.contrib.auth import logout
# from django.contrib.auth import get_user_model
# users = get_user_model()
#
#
# @login_required
# def dashboard(request):
#     tickets = Payment.objects.filter(user=request.user, status='success')
#     return render(request, 'users/dashboard.html', {'tickets': tickets})
# def register(request):
#     if request.method == 'POST':
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('login')
#     else:
#         form = UserCreationForm()
#     return render(request, 'registration/register.html', {'form': form})
#
# @login_required
# def dashboard(request):
#     return render(request, 'users/dashboard.html')
#
# class RegisterView(generics.CreateAPIView):
#     queryset = User.objects.all()
#     permission_classes = [AllowAny]
#     serializer_class = RegisterSerializer
#
# def custom_logout_view(request):
#     if request.method == 'POST':
#         logout(request)
#         return redirect('logged_out')  # redirect to logout success page
#     return render(request, 'registration/logout_confirm.html')
#
#
