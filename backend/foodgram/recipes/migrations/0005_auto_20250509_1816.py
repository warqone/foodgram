# Generated by Django 3.2.3 on 2025-05-09 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_alter_favorite_created'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shoppingcart',
            name='updated',
        ),
        migrations.AlterField(
            model_name='favorite',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления в избранное'),
        ),
    ]
