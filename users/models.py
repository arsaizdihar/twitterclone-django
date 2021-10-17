import graphene
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.core import validators
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .managers import CustomUserManager


# Create your models here.
class User(AbstractUser):
    first_name = None
    last_name = None
    password = models.CharField(_("password"), max_length=128)
    display_name = models.CharField(_("display name"), max_length=50)
    email = models.EmailField(_("email address"), unique=True)
    username = models.CharField(
        _("username"),
        max_length=30,
        unique=True,
        help_text=_("Required. 30 characters or fewer. Letters and digits."),
        validators=[
            validators.RegexValidator(
                r"^[\w]+$",
                _(
                    "Enter a valid username. "
                    "This value may contain only letters and numbers characters."
                ),
                "invalid",
            ),
        ],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    bio = models.TextField(_("User bio"), "bio", blank=True)
    following = models.ManyToManyField(
        "self",
        related_name="followers",
        related_query_name="followers",
        symmetrical=False,
        blank=True,
    )
    photo = models.TextField(_("Profile photo"), blank=True, null=True)
    private = models.BooleanField(default=False)
    follow_requests = models.ManyToManyField("self", symmetrical=False, blank=True)

    objects = CustomUserManager()

    def get_full_name(self):
        return self.display_name

    def get_short_name(self):
        return self.username

    def set_password(self, raw_password):
        if len(raw_password) < 6:
            raise Exception("Minimum password length is 6")
        self.password = make_password(raw_password)

    def __str__(self):
        return self.username
