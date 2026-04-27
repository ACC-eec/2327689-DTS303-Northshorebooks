from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from .forms import UserRegistrationForm
from config.security_logger import log_login_success, log_login_failure


@csrf_protect
def register_view(request):
    """User registration view."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}. Please log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


class CustomLoginView(LoginView):
    """Custom login view with rate limiting."""
    template_name = 'registration/login.html'
    
    def form_valid(self, form):
        """Handle successful login with rate limiting check."""
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        
        # Check rate limiting
        cache_key = f'login_attempts_{self.request.META.get("REMOTE_ADDR")}_{username}'
        attempts = cache.get(cache_key, 0)
        
        if attempts >= 5:
            messages.error(self.request, 'Too many login attempts. Please try again in 5 minutes.')
            log_login_failure(self.request, username)
            return self.form_invalid(form)
        
        user = authenticate(username=username, password=password)
        if user is not None:
            # Reset attempts on success
            cache.delete(cache_key)
            
            # Regenerate session ID on login
            self.request.session.cycle_key()
            
            login(self.request, user)
            log_login_success(self.request, user)
            messages.success(self.request, f'Welcome back, {username}!')
            return redirect(self.get_success_url())
        else:
            # Increment attempts
            cache.set(cache_key, attempts + 1, 300)  # 5 minutes
            log_login_failure(self.request, username)
            # Generic error message
            messages.error(self.request, 'Invalid credentials.')
            return self.form_invalid(form)


class CustomLogoutView(LogoutView):
    """Custom logout view that flushes session."""
    def dispatch(self, request, *args, **kwargs):
        # Flush session completely
        request.session.flush()
        return super().dispatch(request, *args, **kwargs)
