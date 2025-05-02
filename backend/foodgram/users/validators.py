from django.core.exceptions import ValidationError

from users import constants


def validate_username(value):
    if value in constants.BANNED_USERNAMES:
        raise ValidationError(
            f'Имя пользователя {value} недопустимо.')
