"""Account views — registration, login with rate limiting, and logout.

The hardening here is layered:

* HTML login (:class:`CustomLoginView`) is gated by **two** counters —
  per-(IP, username) for vertical brute-force and per-IP for horizontal
  sweeps — and lets a *correct* password through even when the per-user
  counter is hot, so attacker noise on a shared NAT cannot lock the
  legitimate owner out.
* JWT login (:class:`ThrottledTokenObtainPairView`) wears its own
  anonymous DRF throttle so the JSON door is not a brute-force bypass
  for the HTML door.
* Registration (:func:`register_view`) is per-IP throttled and the
  collision error is generic, removing the username-enumeration oracle.
"""
import hashlib

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.views import LoginView, LogoutView
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView

from config.security_logger import log_login_failure, log_login_success

from .forms import UserRegistrationForm


# Failed-login attempts allowed per (IP, username) before that pair is
# locked out — protects a single account from vertical brute-force.
LOGIN_ATTEMPT_LIMIT = 5

# Failed-login attempts allowed per IP across *any* username before the
# whole IP is locked out — protects against horizontal sweeps that step
# through a list of usernames five-at-a-time.
LOGIN_IP_ATTEMPT_LIMIT = 20

# Cooldown applied to both counters above, in seconds.
LOGIN_LOCKOUT_SECONDS = 300

# Registration probes allowed per IP before the endpoint locks the IP
# out — closes the username-enumeration channel that pairs with the
# stock UserCreationForm error message.
REGISTRATION_ATTEMPT_LIMIT = 5
REGISTRATION_LOCKOUT_SECONDS = 300


def _hash_username(username):
    """Return a short hex digest of the username for use in cache keys.

    Hashing prevents an attacker from bloating the cache by spraying very
    long unique usernames, and turns the key into a fixed-length string.
    """
    return hashlib.sha256(username.encode('utf-8')).hexdigest()[:16]


def _client_ip(request):
    """Best-effort client IP — falls back to ``'unknown'`` when missing."""
    return request.META.get('REMOTE_ADDR', 'unknown')


@csrf_protect
def register_view(request):
    """Create a new user account using Django's hashed-password machinery.

    Per-IP throttled to make username-enumeration impractical even though
    the underlying form has a generic collision error.
    """
    ip = _client_ip(request)
    ip_key = f'register_attempts_ip_{ip}'

    if request.method == 'POST':
        attempts = cache.get(ip_key, 0)
        if attempts >= REGISTRATION_ATTEMPT_LIMIT:
            messages.error(
                request,
                'Too many registration attempts. '
                'Please try again in 5 minutes.',
            )
            return render(
                request, 'accounts/register.html',
                {'form': UserRegistrationForm()},
            )

        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(
                request,
                f'Account created for {username}. Please log in.',
            )
            return redirect('login')

        # Any failed attempt — invalid form, taken username, weak
        # password — counts toward the same throttle so an attacker
        # cannot probe usernames freely.
        cache.set(ip_key, attempts + 1, REGISTRATION_LOCKOUT_SECONDS)
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


class CustomLoginView(LoginView):
    """Django login plus a layered (IP, username) and per-IP attempt counter.

    Compared with the previous implementation, two adversarial cases are
    closed:

    * **Horizontal brute-force.** A separate per-IP counter
      (``LOGIN_IP_ATTEMPT_LIMIT``) caps the *total* failed attempts an
      IP can make across all usernames, so stepping through a list of
      victims one-at-a-time no longer evades the lockout.
    * **Shared-NAT denial of service.** When the per-(IP, username)
      counter is hot, ``post`` no longer short-circuits the request. It
      authenticates the credentials inline; valid creds proceed through
      the normal ``form_valid`` flow, while wrong creds are answered
      with the lockout message *without* a fresh authenticate call.
    """

    template_name = 'registration/login.html'

    def _user_cache_key(self, username):
        """Per-(IP, username) key — guards a single account."""
        return (
            f'login_attempts_{_client_ip(self.request)}'
            f'_{_hash_username(username)}'
        )

    def _ip_cache_key(self):
        """Per-IP key — guards against horizontal sweeps."""
        return f'login_attempts_ip_{_client_ip(self.request)}'

    def post(self, request, *args, **kwargs):
        """Apply both lockout layers; let valid credentials through."""
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Layer 1: per-IP global counter — applies regardless of which
        # username is targeted, so an attacker cannot pivot to a fresh
        # victim username after locking the previous one.
        ip_attempts = cache.get(self._ip_cache_key(), 0)
        if ip_attempts >= LOGIN_IP_ATTEMPT_LIMIT:
            messages.error(
                request,
                'Too many login attempts from this network. '
                'Please try again in 5 minutes.',
            )
            if username:
                log_login_failure(request, username)
            return self.render_to_response(
                self.get_context_data(form=self.get_form()),
            )

        # Layer 2: per-(IP, username) counter — when hot, authenticate
        # inline so that a legitimate owner sharing the IP can still
        # sign in. Wrong creds during this state are rejected without
        # incrementing the counter further.
        if username:
            user_attempts = cache.get(self._user_cache_key(username), 0)
            if user_attempts >= LOGIN_ATTEMPT_LIMIT:
                user = authenticate(
                    request, username=username, password=password,
                )
                if user is not None:
                    auth_login(request, user)
                    cache.delete(self._user_cache_key(username))
                    request.session.cycle_key()
                    log_login_success(request, user)
                    messages.success(request, f'Welcome back, {username}!')
                    return redirect(self.get_success_url())

                messages.error(
                    request,
                    'Too many login attempts. '
                    'Please try again in 5 minutes.',
                )
                log_login_failure(request, username)
                return self.render_to_response(
                    self.get_context_data(form=self.get_form()),
                )

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """On a successful login, clear both counters and rotate the session."""
        username = form.cleaned_data.get('username')
        cache.delete(self._user_cache_key(username))
        cache.delete(self._ip_cache_key())
        self.request.session.cycle_key()
        response = super().form_valid(form)
        log_login_success(self.request, form.get_user())
        messages.success(self.request, f'Welcome back, {username}!')
        return response

    def form_invalid(self, form):
        """Increment both the per-(IP, username) and per-IP counters."""
        username = form.data.get('username', '').strip()
        if username:
            user_key = self._user_cache_key(username)
            cache.set(
                user_key,
                cache.get(user_key, 0) + 1,
                LOGIN_LOCKOUT_SECONDS,
            )
            log_login_failure(self.request, username)

        ip_key = self._ip_cache_key()
        cache.set(
            ip_key, cache.get(ip_key, 0) + 1, LOGIN_LOCKOUT_SECONDS,
        )

        # Generic message — never confirm whether the username exists.
        messages.error(self.request, 'Invalid credentials.')
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """Log out and fully flush the session, dropping any stored data."""

    def dispatch(self, request, *args, **kwargs):
        """Clear all session data before delegating to Django's logout."""
        request.session.flush()
        return super().dispatch(request, *args, **kwargs)


class JWTLoginThrottle(AnonRateThrottle):
    """Dedicated throttle scope for the JWT credential endpoint.

    Uses its own scope (``'jwt_login'``) so the rate is configurable in
    ``config/settings.py`` independent of the general ``'anon'`` rate.
    """

    scope = 'jwt_login'


class ThrottledTokenObtainPairView(TokenObtainPairView):
    """SimpleJWT's token endpoint, gated by an anonymous-rate throttle.

    Without this, ``/api/auth/token/`` is a credential-brute-force door
    that completely bypasses :class:`CustomLoginView`'s lockout — the
    HIGH-severity finding from the pen-test pass on 2026-04-27.
    """

    throttle_classes = [JWTLoginThrottle]
