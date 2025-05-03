from django.db import models
from django.contrib.auth import get_user_model

from recipes import constants

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название тега',
        max_length=constants.MAX_TITLE_LENGTH
    )
    slug = models.SlugField(
        verbose_name='Слаг тега',
        max_length=constants.MAX_TITLE_LENGTH
    )


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=constants.MAX_TITLE_LENGTH
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=constants.MAX_TITLE_LENGTH
    )


class Recipe(models.Model):
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты'
    )
    is_favorited = models.BooleanField(
        'Добавлено в избранное',
        default=False
    )
    is_in_shopping_cart = models.BooleanField(
        'Добавлено в корзину',
        default=False)
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=constants.MAX_TITLE_LENGTH
    )
    string = models.CharField(
        verbose_name='Описание рецепта'
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления'
    )


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    created = models.DateTimeField(
        verbose_name='Дата добавления в избранное'
    )
    updated = models.DateTimeField(
        verbose_name='Дата обновления в избранное'
    )
    
    class Meta:
        unique_together = ('user', 'recipe')
        ordering = ('-created',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    created = models.DateTimeField(
        verbose_name='Дата добавления в корзину'
    )
    updated = models.DateTimeField(
        verbose_name='Дата обновления в корзину'
    )
    
    class Meta:
        unique_together = ('user', 'recipe')
        ordering = ('-created',)
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
