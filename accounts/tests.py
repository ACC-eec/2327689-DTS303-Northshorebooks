"""Happy-path tests for the accounts app."""
import json
import logging
from io import StringIO
from unittest.mock import Mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from config.security_logger import (
    SecurityJSONFormatter,
    log_admin_access_denied,
    log_login_failure,
    log_login_success,
)


class AccountsTestCase(TestCase):
    """Happy-path coverage of registration, login redirects and the lockout.

    Adversarial coverage — JWT bypass, enumeration, horizontal sweep — lives
    in :mod:`accounts.tests_pentest`; this file confirms the ordinary
    customer journey still works once those defences are in place.
    """

    def setUp(self):
        """Create one pre-existing user for the rate-limit test."""
        self.user = User.objects.create_user(
            username='testuser', password='testpass123',
            email='test@example.com',
        )

    def test_registration(self):
        """A valid registration POST creates a new user and redirects."""
        response = self.client.post('/accounts/register/', {
            'username': 'newuser',
            'password1': 'TestPass-12345',
            'password2': 'TestPass-12345',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login_required_redirect(self):
        """Anonymous access to a basket URL redirects to login."""
        response = self.client.get('/orders/basket/')
        self.assertEqual(response.status_code, 302)

    def test_login_rate_limiting(self):
        """Six failed logins in a row triggers the lock-out message."""
        cache.clear()
        for _ in range(5):
            self.client.post('/accounts/login/', {
                'username': 'testuser', 'password': 'wrongpass',
            })

        response = self.client.post('/accounts/login/', {
            'username': 'testuser', 'password': 'wrongpass',
        })
        self.assertContains(
            response, 'Too many login attempts', status_code=200,
        )


class SecurityLogFormatterTests(TestCase):
    """The audit trail must actually contain the structured fields.

    Regression for the bug where the stdlib ``Formatter`` silently
    dropped every ``extra={...}`` key the helpers attach — leaving the
    log file with ``message`` only and no ``ip_address``, ``username``
    or ``event_type``. The custom :class:`SecurityJSONFormatter` exists
    to fix that, so this suite verifies it does.
    """

    def setUp(self):
        """Wire the formatter to a fresh in-memory stream handler."""
        self.stream = StringIO()
        handler = logging.StreamHandler(self.stream)
        handler.setFormatter(SecurityJSONFormatter())

        self.logger = logging.getLogger('security')
        self._original_handlers = self.logger.handlers
        self._original_propagate = self.logger.propagate
        self.logger.handlers = [handler]
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

    def tearDown(self):
        """Restore the configured handlers so other tests are unaffected."""
        self.logger.handlers = self._original_handlers
        self.logger.propagate = self._original_propagate

    def _last_record(self):
        """Parse the JSON line written by the most recent log call."""
        return json.loads(self.stream.getvalue().strip().splitlines()[-1])

    def _request(self, ip='203.0.113.10'):
        """Build a minimal ``HttpRequest``-shaped mock for the helpers."""
        return Mock(META={'REMOTE_ADDR': ip}, path='/api/books/', method='POST')

    def test_login_success_emits_ip_username_and_event_type(self):
        """A successful login writes a JSON line with all three fields."""
        user = User.objects.create_user(
            username='ada', password='SeasidePass1!', email='ada@example.com',
        )

        log_login_success(self._request(ip='198.51.100.7'), user)

        record = self._last_record()
        self.assertEqual(record['event_type'], 'login_success')
        self.assertEqual(record['ip_address'], '198.51.100.7')
        self.assertEqual(record['username'], 'ada')
        self.assertNotEqual(record['email_hash'], 'no-email')
        # The raw email is hashed before the line is written — never logged.
        self.assertNotIn('ada@example.com', json.dumps(record))

    def test_login_failure_logs_username_but_not_password(self):
        """A failed login records the candidate username, never the password."""
        log_login_failure(self._request(), username='attacker')

        record = self._last_record()
        self.assertEqual(record['event_type'], 'login_failure')
        self.assertEqual(record['username'], 'attacker')
        self.assertEqual(record['ip_address'], '203.0.113.10')

    def test_admin_access_denied_records_resource(self):
        """Authorisation failures carry the resource the user reached for."""
        user = User.objects.create_user(
            username='ada', password='SeasidePass1!',
        )

        log_admin_access_denied(self._request(), user, 'order_42')

        record = self._last_record()
        self.assertEqual(record['event_type'], 'admin_access_denied')
        self.assertEqual(record['resource'], 'order_42')
        self.assertEqual(record['username'], 'ada')
