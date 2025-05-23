from django.conf import settings
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
                    'Имя пользователя может содержать только буквы, '
                    'цифры и символы @/./+/-/_'
                )
            )
        ]
    )
    role = models.CharField(
        'Роль',
        max_length=constants.ROLE_NAME_LENGTH,
        choices=constants.ROLE_CHOICES,
        default=constants.USER,
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to=settings.AVATAR_PATH,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.username[:constants.USERNAME_LENGTH]

    @property
    def is_admin(self):
        return self.role == constants.ADMIN or self.is_superuser


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_subscription'
            )
        ]
        ordering = ('-created_at',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
