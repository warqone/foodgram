from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from rest_framework import serializers

from users import constants

User = get_user_model()


class SignUpSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        max_length=constants.EMAIL_LENGTH)
    username = serializers.CharField(
        required=True,
        max_length=constants.USERNAME_LENGTH,
        validators=[
            RegexValidator(
                regex=constants.USERNAME_VALIDATOR,
                message=(
                    'Имя пользователя может содержать только буквы, цифры и '
                    'символы @/./+/-/_'),
                code='invalid_username'
            )
        ]
    )
    first_name = serializers.CharField(
        required=True,
        max_length=constants.USERNAME_LENGTH
    )
    last_name = serializers.CharField(
        required=True,
        max_length=constants.USERNAME_LENGTH
    )
    password = serializers.CharField(
        required=True,
        max_length=constants.PASSWORD_LENGTH
    )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким именем уже существует.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует.')
        return value

    def validate_role(self, value):
        if self.context['request'].user.is_admin:
            return value
        return constants.USER
