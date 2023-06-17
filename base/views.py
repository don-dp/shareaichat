from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .forms import EmailUpdateForm
from django.contrib.auth.views import LoginView, PasswordResetView
from .helpers import check_turnstile

def handler400(request, exception, template_name="base/error.html"):
    return render(request, template_name, status=400)

def handler403(request, exception, template_name="base/error.html"):
    return render(request, template_name, status=403)

def handler404(request, exception, template_name="base/error.html"):
    return render(request, template_name, status=404)

def handler500(request, template_name="base/error.html"):
    return render(request, template_name, status=500)

class HomePage(View):
    def get(self, request):
        return render(request, "base/homepage.html", {})

class AboutPage(View):
    def get(self, request):
        return render(request, "base/aboutpage.html", {})

class SignupView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You are already logged in, so you can\'t signup. If you want to create a new account logout first.')
            return redirect('homepage')
        
        form = UserCreationForm()
        return render(request, 'registration/signup.html', {'form': form})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You are already logged in, so you can\'t signup. If you want to create a new account, logout first.')
            return redirect('homepage')
        
        if not check_turnstile(request):
            return redirect('signup')
        
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.info(request, 'Successfully registered. You can update your email in the profile page.')
            return redirect('homepage')
        return render(request, 'registration/signup.html', {'form': form})

class ProfileView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login')

    def get(self, request, *args, **kwargs):
        form = EmailUpdateForm(initial={'email': request.user.email})
        return render(request, 'base/profile.html', {'user': request.user, 'form': form})

    def post(self, request, *args, **kwargs):
        form = EmailUpdateForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            request.user.email = email
            request.user.save()
            messages.success(request, 'Email updated successfully')
        else:
            messages.error(request, 'Invalid email')
        return redirect('profile')

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def post(self, request, *args, **kwargs):
        if check_turnstile(request):
            return super().post(request, *args, **kwargs)
        else:
            return redirect('login')

class CustomPasswordResetView(PasswordResetView):
    def post(self, request, *args, **kwargs):
        if not check_turnstile(request):
            return redirect('password_reset')
        return super().post(request, *args, **kwargs)