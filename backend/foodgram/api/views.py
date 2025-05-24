from django.contrib.auth import get_user_model
from django.db.models import (BooleanField, Count, Exists, OuterRef, Sum,
                              Value)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from rest_framework import filters, pagination, permissions, response, status
from rest_framework.decorators import action
from rest_framework import viewsets

from api import serializers
from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с пользователями.

    Выводит список пользователей и позволяет создавать новых.
    Пагинация и поиск по username и email.
    """

    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    pagination_class = pagination.LimitOffsetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^username', '^email')
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_serializer_class(self):
        """Возвращает класс сериализатора для текущего действия."""
        return (serializers.UserCreateSerializer
                if self.action == 'create'
                else serializers.UserSerializer)

    @action(detail=False, methods=['get'], url_path='me',
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Возвращает информацию о текущем пользователе."""
        serializer = self.get_serializer(request.user)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='set_password',
            permission_classes=[permissions.IsAuthenticated])
    def set_password(self, request):
        """Устанавливает новый пароль для текущего пользователя."""
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar',
            permission_classes=[permissions.IsAuthenticated])
    def avatar(self, request):
        """Устанавливает или удаляет аватарку для текущего пользователя."""
        user = request.user

        if request.method == 'PUT':
            serializer = serializers.AvatarSerializer(
                user, data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return response.Response(
                serializer.data, status=status.HTTP_200_OK)

        user.avatar.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscribe(self, request, pk=None):
        """Подписывается на автора."""
        user = request.user

        if request.method == 'POST':
            author = get_object_or_404(User, pk=pk)
            serializer = serializers.SubscriptionCreateSerializer(
                data={'author': author.id},
                context={
                    'request': request,
                    'recipes_limit': request.query_params.get('recipes_limit'),
                },
            )
            serializer.is_valid(raise_exception=True)
            subscription = serializer.save()

            out_serializer = serializers.SubscriptionSerializer(
                subscription,
                context={
                    'request': request,
                    'recipes_limit': request.query_params.get('recipes_limit'),
                },
            )
            return response.Response(out_serializer.data,
                                     status=status.HTTP_201_CREATED)

        deleted, _ = (Subscription.objects.filter(
            user=user, author_id=pk).delete())

        if deleted:
            return response.Response(status=status.HTTP_204_NO_CONTENT)

        return response.Response(
            {'errors': 'Вы не подписаны на этого пользователя'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[permissions.IsAuthenticated],
        pagination_class=pagination.LimitOffsetPagination,
    )
    def subscriptions(self, request):
        """Получает подписки текущего пользователя."""
        queryset = (User.objects
                    .filter(subscribers__user=request.user)
                    .annotate(recipes_count=Count('recipes')))

        page = self.paginate_queryset(queryset)

        serializer = serializers.SubscriptionSerializer(
            page if page is not None else queryset,
            many=True,
            context={
                'request': request,
                'recipes_limit': request.query_params.get('recipes_limit'),
            },
        )

        return (self.get_paginated_response(serializer.data)
                if page is not None
                else response.Response(serializer.data,
                                       status=status.HTTP_200_OK))


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Теги ― только чтение."""

    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('slug',)
    pagination_class = None
    http_method_names = ['get']


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Ингредиенты ― только чтение, поиск по названию."""

    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)
    pagination_class = None
    http_method_names = ['get']


class RecipeViewSet(viewsets.ModelViewSet):
    """Полный CRUD для рецептов.

    Доп. экшены: избранное, корзина, короткая ссылка, выгрузка корзины.
    """

    serializer_class = serializers.RecipeSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly
    ]
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = RecipeFilter
    search_fields = ('name', 'text')

    def toggle_relation(
        self,
        relation_model,
        serializer_class,
        request,
        pk,
    ):
        """Добавляет или удаляет рецепт из избранного или корзины."""
        user = request.user

        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, pk=pk)

            serializer = serializer_class(
                data={'recipe': recipe.id},
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            short = serializers.ShortRecipeSerializer(
                recipe, context={'request': request}
            )
            return response.Response(
                short.data, status=status.HTTP_201_CREATED)

        deleted, _ = (relation_model.objects.filter(
            user=user, recipe_id=pk).delete())

        if deleted:
            return response.Response(status=status.HTTP_204_NO_CONTENT)

        return response.Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite',
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавление и удаление рецепта из избранного."""
        return self.toggle_relation(
            relation_model=Favorite,
            serializer_class=serializers.FavoriteSerializer,
            request=request,
            pk=pk,
        )

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart',
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавление и удаление рецепта из корзины."""
        return self.toggle_relation(
            relation_model=ShoppingCart,
            serializer_class=serializers.ShoppingCartSerializer,
            request=request,
            pk=pk,
        )

    @action(detail=True, methods=['get'], url_path='get-link',
            permission_classes=[permissions.AllowAny])
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = get_object_or_404(Recipe, pk=pk)
        return response.Response({'short-link': recipe.get_short_url()},
                                 status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart',
            permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        """Выгрузка списка покупок."""
        ingredients_qs = (
            RecipeIngredient.objects
            .filter(recipe__shoppingcarts__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total=Sum('amount'))
            .order_by('ingredient__name')
        )

        buffer = self.build_shopping_list(ingredients_qs)
        rsp = HttpResponse(
            buffer.getvalue(),
            content_type='text/plain; charset=utf-8',
        )
        rsp['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return rsp

    @staticmethod
    def build_shopping_list(ingredients_qs):
        """Сборка списка покупок."""
        from io import StringIO
        buff = StringIO()
        for row in ingredients_qs:
            buff.write(
                f'{row["ingredient__name"]} '
                f'({row["ingredient__measurement_unit"]}) – {row["total"]}\n'
            )
        buff.seek(0)
        return buff

    def get_serializer_class(self):
        """Выбор сериализатора."""
        return (serializers.RecipeCreateUpdateSerializer
                if self.action in ('create', 'update', 'partial_update')
                else serializers.RecipeSerializer)

    def perform_create(self, serializer):
        """Установка автора."""
        serializer.save(author=self.request.user)

    def get_queryset(self):
        """Получение списка рецептов.

        Аннотируем рецепты с информацией о том, добавлен ли рецепт в
        избранное и корзину.
        """
        qs = (Recipe.objects
              .select_related('author')
              .prefetch_related('tags',
                                'recipe_ingredients__ingredient'))

        user = self.request.user
        if user.is_authenticated:
            fav_subq = Favorite.objects.filter(
                user=user, recipe=OuterRef('pk'))
            cart_subq = ShoppingCart.objects.filter(
                user=user, recipe=OuterRef('pk'))
            qs = qs.annotate(is_favorited=Exists(fav_subq),
                             is_in_shopping_cart=Exists(cart_subq))
        else:
            qs = qs.annotate(
                is_favorited=Value(False, output_field=BooleanField()),
                is_in_shopping_cart=Value(False, output_field=BooleanField()))
        return qs
