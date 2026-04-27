"""
Security logging utility for tracking security events.
"""
import logging
import hashlib
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger('security')


def _hash_email(email: str) -> str:
    """Hash email for logging (minimal PII)."""
    if not email:
        return 'no-email'
    return hashlib.sha256(email.encode()).hexdigest()[:16]


def log_login_success(request, user):
    """Log successful login attempt."""
    email_hash = _hash_email(getattr(user, 'email', ''))
    logger.info(
        f'login_success',
        extra={
            'event_type': 'login_success',
            'user_id': user.id if user.is_authenticated else None,
            'username': user.username if user.is_authenticated else None,
            'email_hash': email_hash,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
        }
    )


def log_login_failure(request, username=None):
    """Log failed login attempt."""
    logger.warning(
        f'login_failure',
        extra={
            'event_type': 'login_failure',
            'username': username,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
        }
    )


def log_admin_access_denied(request, user, resource):
    """Log denied admin access attempt."""
    email_hash = _hash_email(getattr(user, 'email', '')) if user.is_authenticated else None
    logger.warning(
        f'admin_access_denied',
        extra={
            'event_type': 'admin_access_denied',
            'user_id': user.id if user.is_authenticated else None,
            'username': user.username if user.is_authenticated else None,
            'email_hash': email_hash,
            'resource': resource,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
        }
    )


def log_csrf_failure(request):
    """Log CSRF token validation failure."""
    logger.warning(
        f'csrf_failure',
        extra={
            'event_type': 'csrf_failure',
            'path': request.path,
            'method': request.method,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
        }
    )


def log_suspicious_input(request, input_type, value):
    """Log suspicious input patterns (careful not to block legitimate input)."""
    # Only log, don't block - this is for monitoring
    logger.warning(
        f'suspicious_input',
        extra={
            'event_type': 'suspicious_input',
            'input_type': input_type,
            'value_preview': str(value)[:100],  # Limit length
            'path': request.path,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
        }
    )


def log_session_mismatch(request, user):
    """Log session mismatch (e.g., user-agent change)."""
    email_hash = _hash_email(getattr(user, 'email', '')) if user.is_authenticated else None
    logger.warning(
        f'session_mismatch',
        extra={
            'event_type': 'session_mismatch',
            'user_id': user.id if user.is_authenticated else None,
            'username': user.username if user.is_authenticated else None,
            'email_hash': email_hash,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
        }
    )
