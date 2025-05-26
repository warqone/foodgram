from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка для модели User.

    Позволяет просматривать, фильтровать и поиск пользователей.
    """

    list_display = ('username', 'email', 'role')
    list_filter = ('role', 'is_active', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    empty_value_display = '-пусто-'
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Персональная информация', {'fields': (
            'first_name', 'last_name', 'role')}),
    )
