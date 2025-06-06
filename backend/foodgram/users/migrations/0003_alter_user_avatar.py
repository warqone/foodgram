# Generated by Django 3.2.3 on 2025-05-03 20:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='avatar',
            field=models.ImageField(blank=True, default='media/users/default.png', null=True, upload_to='media/users/', verbose_name='Аватар'),
        ),
    ]
