from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from users import constants, validators


class User(AbstractUser):
    username = models.CharField(
        'Имя пользователя',
        max_length=constants.USERNAME_LENGTH,
        unique=True,
        validators=[
            validators.validate_username,
            RegexValidator(
                regex=constants.USERNAME_VALIDATOR,
                message=(
                    'Имя пользователя может содержать только буквы, цифры и '
                    'символы @/./+/-/_')),
        ]
    )
    role = models.CharField(
        'Роль',
        max_length=constants.ROLE_NAME_LENGTH,
        choices=constants.ROLE_CHOICES,
        default=constants.USER,
    )

    def __str__(self):
        return self.username[:constants.USERNAME_LENGTH]

    @property
    def is_admin(self):
        return self.role == constants.ADMIN or self.is_superuser
