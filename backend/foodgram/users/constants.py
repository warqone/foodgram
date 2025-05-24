EMAIL_LENGTH = 254
USERNAME_LENGTH = 150
NAME_LENGTH = 150
USERNAME_VALIDATOR = r'^[\w.@+-]+\Z'
PASSWORD_LENGTH = 128
BANNED_USERNAMES = ['me', 'admin', 'root']
ROLE_NAME_LENGTH = 10
USER = 'user'
ADMIN = 'admin'
ROLE_CHOICES = (
    (USER, 'Пользователь'),
    (ADMIN, 'Администратор'),
)
