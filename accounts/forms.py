"""Forms for the accounts app."""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class UserRegistrationForm(UserCreationForm):
    """Registration form — extends the built-in form with an optional email.

    Password handling and validation is delegated to
    :class:`django.contrib.auth.forms.UserCreationForm`, which uses
    Django's PBKDF2 hasher and the configured password validators.

    The ``clean_username`` override below replaces Django's stock
    ``"A user with that username already exists."`` with a generic
    error so the form can no longer be used as a username-enumeration
    oracle.
    """

    # Generic error reused for any username problem. The throttled view
    # in :func:`accounts.views.register_view` provides the second half
    # of this defence by capping probes per IP.
    GENERIC_USERNAME_ERROR = (
        'This username is unavailable. Please choose a different one.'
    )

    email = forms.EmailField(required=False, help_text='Optional')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        """Customise help text on the inherited username/password fields."""
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = (
            'Required. 150 characters or fewer. Letters, digits and '
            '@/./+/-/_ only.'
        )
        self.fields['password1'].help_text = (
            'Your password must contain at least 10 characters.'
        )

    def clean_username(self):
        """Return the cleaned username or raise a non-leaky validation error.

        Django's default behaviour distinguishes "username taken" from
        "username invalid" — that distinction is the enumeration oracle
        the pen-test exploited. Both branches now raise the same string.
        """
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError(self.GENERIC_USERNAME_ERROR)
        return username
