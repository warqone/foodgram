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

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с пользователями.
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
        return (serializers.UserCreateSerializer
                if self.action == 'create'
                else serializers.UserSerializer)

    @action(detail=False, methods=['get'], url_path='me',
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='set_password',
            permission_classes=[permissions.IsAuthenticated])
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar',
            permission_classes=[permissions.IsAuthenticated])
    def avatar(self, request):
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

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe',
            permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        user = request.user

        if request.method == 'POST':
            serializer = serializers.SubscriptionCreateSerializer(
                data={'author': pk},
                context={
                    'request': request,
                    'recipes_limit': request.query_params.get('recipes_limit'),
                },
            )
            serializer.is_valid(raise_exception=True)
            author = serializer.save()

            out_serializer = serializers.SubscriptionSerializer(
                author,
                context={
                    'request': request,
                    'recipes_limit': request.query_params.get('recipes_limit'),
                },
            )
            return response.Response(out_serializer.data,
                                     status=status.HTTP_201_CREATED)

        deleted, _ = user.subscriptions.filter(author_id=pk).delete()
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
    """
    Полный CRUD для рецептов.
    Доп. экшены: избранное, корзина, короткая ссылка, выгрузка корзины.
    """
    serializer_class = serializers.RecipeSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly
    ]
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = RecipeFilter
    search_fields = ('name', 'text')

    def toggle_relation(self, model, request, pk,
                        duplicate_msg, not_found_msg):
        recipe = get_object_or_404(Recipe, pk=pk)
        instance, created = model.objects.get_or_create(
            user=request.user, recipe=recipe)

        if request.method == 'POST':
            if not created:
                return response.Response({'errors': duplicate_msg},
                                         status=status.HTTP_400_BAD_REQUEST)
            return response.Response(
                serializers.ShortRecipeSerializer(recipe).data,
                status=status.HTTP_201_CREATED)

        if created:
            instance.delete()
            return response.Response({'errors': not_found_msg},
                                     status=status.HTTP_400_BAD_REQUEST)

        instance.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite',
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        return self.toggle_relation(
            Favorite, request, pk,
            duplicate_msg='Рецепт уже в избранном',
            not_found_msg='Рецепт не найден в избранном'
        )

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart',
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self.toggle_relation(
            ShoppingCart, request, pk,
            duplicate_msg='Рецепт уже в списке покупок',
            not_found_msg='Рецепт не найден в корзине'
        )

    @action(detail=True, methods=['get'], url_path='get-link',
            permission_classes=[permissions.AllowAny])
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        return response.Response({'short-link': recipe.get_short_url()},
                                 status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart',
            permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients_qs = (RecipeIngredient.objects
                          .filter(recipe__shoppingcarts__user=request.user)
                          .values('ingredient__name',
                                  'ingredient__measurement_unit')
                          .annotate(total=Sum('amount'))
                          .order_by('ingredient__name'))

        if not ingredients_qs.exists():
            return HttpResponse('Ваша корзина пуста',
                                content_type='text/plain; charset=utf-8',
                                status=status.HTTP_400_BAD_REQUEST)

        buffer = self.build_shopping_list(ingredients_qs)
        rsp = HttpResponse(buffer.getvalue(),
                           content_type='text/plain; charset=utf-8')
        rsp['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return rsp

    @staticmethod
    def build_shopping_list(ingredients_qs):
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
        return (serializers.RecipeCreateUpdateSerializer
                if self.action in ('create', 'update', 'partial_update')
                else serializers.RecipeSerializer)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
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
