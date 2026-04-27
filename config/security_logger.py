"""Security logger — a thin façade over Python ``logging`` for the events
worth keeping in a separate file.

Every helper here writes one structured record to the ``'security'``
logger (configured in :mod:`config.settings` to land at
``storage/logs/security.log`` as JSON-per-line). Keeping a separate log
means a future log-aggregator can be pointed at security-relevant
events alone, without sifting through ordinary application chatter.

A note on PII: emails are hashed before they touch the file. The
investigator who needs to map a hash back to a real customer can do so
through the live database, which is the right place for that lookup to
live.
"""
import hashlib
import json
import logging

logger = logging.getLogger('security')


class SecurityJSONFormatter(logging.Formatter):
    """Render a ``LogRecord`` as one JSON object, including ``extra`` keys.

    Python's stdlib ``Formatter`` only emits the attributes named in its
    format string; the structured fields the helpers below attach via
    ``extra={...}`` would otherwise be silently dropped on the way to
    disk. This formatter promotes a known set of those fields into the
    output so the audit trail actually contains ``event_type``,
    ``ip_address``, ``username`` and friends.
    """

    EXTRA_FIELDS = (
        'event_type', 'user_id', 'username', 'email_hash', 'ip_address',
        'resource', 'path', 'method', 'input_type', 'value_preview',
    )

    def format(self, record):
        payload = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'funcName': record.funcName,
            'lineno': record.lineno,
        }
        for key in self.EXTRA_FIELDS:
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, default=str)


def _hash_email(email: str) -> str:
    """Return a sixteen-character SHA-256 digest of an email address.

    The full address never reaches the log — only this stable, opaque
    identifier, which is enough to correlate events across entries.
    """
    if not email:
        return 'no-email'
    return hashlib.sha256(email.encode()).hexdigest()[:16]


def log_login_success(request, user):
    """Record a successful authentication — username, hashed email, IP."""
    email_hash = _hash_email(getattr(user, 'email', ''))
    logger.info(
        'login_success',
        extra={
            'event_type': 'login_success',
            'user_id': user.id if user.is_authenticated else None,
            'username': user.username if user.is_authenticated else None,
            'email_hash': email_hash,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
        }
    )


def log_login_failure(request, username=None):
    """Record a failed authentication — candidate username and IP only.

    The candidate password never appears in the log; a leaked log file
    must not double as a credential dump.
    """
    logger.warning(
        'login_failure',
        extra={
            'event_type': 'login_failure',
            'username': username,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
        }
    )


def log_admin_access_denied(request, user, resource):
    """Record an authorisation failure on a staff-only path.

    Useful for catching the customer probing admin URLs by hand and the
    forgotten test client still pointed at production after a deploy.
    """
    email_hash = _hash_email(getattr(user, 'email', '')) if user.is_authenticated else None
    logger.warning(
        'admin_access_denied',
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
    """Record a CSRF rejection — the path, the verb, the client IP."""
    logger.warning(
        'csrf_failure',
        extra={
            'event_type': 'csrf_failure',
            'path': request.path,
            'method': request.method,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
        }
    )


def log_suspicious_input(request, input_type, value):
    """Record an input that pattern-matches as hostile, without blocking it.

    The intent is monitoring, not enforcement — false positives here are
    cheap, but a false-positive *block* would be a self-inflicted denial
    of service against a legitimate customer.
    """
    # Record the event; never reject the request on the strength of it.
    logger.warning(
        'suspicious_input',
        extra={
            'event_type': 'suspicious_input',
            'input_type': input_type,
            'value_preview': str(value)[:100],  # Limit length
            'path': request.path,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
        }
    )


def log_session_mismatch(request, user):
    """Record a session anomaly — typically a user-agent or IP change.

    Not enforced; a legitimate customer changes browser too. The record
    is here so the pattern can be reviewed after the fact rather than
    acted on in the moment.
    """
    email_hash = _hash_email(getattr(user, 'email', '')) if user.is_authenticated else None
    logger.warning(
        'session_mismatch',
        extra={
            'event_type': 'session_mismatch',
            'user_id': user.id if user.is_authenticated else None,
            'username': user.username if user.is_authenticated else None,
            'email_hash': email_hash,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
        }
    )
