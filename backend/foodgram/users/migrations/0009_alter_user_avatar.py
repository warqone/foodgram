# Generated by Django 3.2.3 on 2025-05-10 14:38

import pathlib

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_user_shopping_cart'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to=pathlib.PureWindowsPath('C:/Dev/sprint18/foodgram/backend/foodgram/media/users/avatar'), verbose_name='Аватар'),
        ),
    ]
