from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Count
from djoser.serializers import SetPasswordSerializer
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from rest_framework import (
    viewsets, permissions, pagination, response, status, filters)
from rest_framework.decorators import action

from api import serializers
from api.filters import IngredientFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer, TagSerializer, IngredientSerializer, RecipeSerializer,
    RecipeCreateUpdateSerializer, SubscriptionSerializer,
    ShortRecipeSerializer)
from recipes.models import Recipe, Tag, Ingredient, Favorite, ShoppingCart

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с пользователями.
    Выводит список пользователей и позволяет создавать новых.
    Пагинация и поиск по username и email.
    """
    permission_classes = (permissions.AllowAny,)
    pagination_class = pagination.LimitOffsetPagination
    queryset = User.objects.all()
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^username', '^email')
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.UserCreateSerializer
        return serializers.UserSerializer

    @action(detail=False, methods=['get'], url_path='me',
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='set_password',
            permission_classes=[permissions.IsAuthenticated])
    def set_password(self, request, *args, **kwargs):
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data["new_password"])
        self.request.user.save()
        return response.Response(
            status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar',
            permission_classes=[permissions.IsAuthenticated])
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user, data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return response.Response(
                serializer.data, status=status.HTTP_200_OK
            )
        elif request.method == 'DELETE':
            user.avatar.delete()
            user.save()
            return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated],
            url_path='subscribe')
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            if user == author:
                return response.Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if user.subscriptions.filter(pk=author.pk).exists():
                return response.Response(
                    {'errors': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.subscriptions.add(author)
            serializer = SubscriptionSerializer(
                author,
                context={
                    'request': request,
                    'recipes_limit': request.query_params.get('recipes_limit')
                }
            )
            return response.Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        elif request.method == 'DELETE':
            if not user.subscriptions.filter(pk=author.pk).exists():
                return response.Response(
                    {'errors': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.subscriptions.remove(author)
            return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='subscriptions',
            permission_classes=[permissions.IsAuthenticated],
            pagination_class=pagination.LimitOffsetPagination)
    def subscriptions(self, request):
        user = request.user
        queryset = user.subscriptions.annotate(
            recipes_count=Count('recipes')).all()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = SubscriptionSerializer(
                page,
                many=True,
                context={
                    'request': request,
                    'recipes_limit': request.query_params.get('recipes_limit')
                }
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(
            queryset,
            many=True,
            context={
                'request': request,
                'recipes_limit': request.query_params.get('recipes_limit')
            }
        )
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ModelViewSet):
    """
    Обрабатывает теги. Только чтение для всех пользователей.
    Фильтрация по slug.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['slug']
    pagination_class = None
    http_method_names = ['get']


class IngredientViewSet(viewsets.ModelViewSet):
    """
    Обрабатывает ингредиенты. Только чтение для всех пользователей.
    Поиск по названию ингредиента.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)
    http_method_names = ['get']
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Обрабатывает рецепты с полным CRUD для авторизованных пользователей.
    Фильтрация по: тегам, автору, избранному, списку покупок.
    """
    queryset = Recipe.objects.all()
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly & IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['tags__slug', 'author__id']
    search_fields = ['name', 'text']

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated],
            url_path='favorite')
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if Favorite.objects.filter(
                    recipe=recipe, user=request.user).exists():
                return response.Response(
                    {'errors': 'Рецепт уже добавлен в избранное'},
                    status=status.HTTP_400_BAD_REQUEST)
            Favorite.objects.create(recipe=recipe, user=request.user)
            return response.Response(
                ShortRecipeSerializer(recipe).data,
                status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            try:
                favorite = Favorite.objects.get(
                    recipe=recipe, user=request.user)
                favorite.delete()
            except Favorite.DoesNotExist:
                return response.Response(
                    {'errors': 'Рецепт не найден в избранном'},
                    status=status.HTTP_400_BAD_REQUEST)
            return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated],
            url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                    recipe=recipe, user=request.user).exists():
                return response.Response(
                    {'errors': 'Рецепт уже добавлен в список покупок'},
                    status=status.HTTP_400_BAD_REQUEST)
            ShoppingCart.objects.create(recipe=recipe, user=request.user)
            return response.Response(
                ShortRecipeSerializer(recipe).data,
                status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            try:
                shopping_cart = ShoppingCart.objects.get(
                    recipe=recipe, user=request.user)
                shopping_cart.delete()
            except ShoppingCart.DoesNotExist:
                return response.Response(
                    {'errors': 'Список покупок не найден.'},
                    status=status.HTTP_400_BAD_REQUEST)
            return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['get'],
            permission_classes=[permissions.AllowAny],
            url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        return response.Response({'short-link': recipe.get_link()},
                                 status=status.HTTP_200_OK)

    @action(detail=False,
            methods=['get'],
            permission_classes=[permissions.IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        shopping_cart_items = ShoppingCart.objects.filter(
            user=request.user
        ).select_related('recipe').prefetch_related(
            'recipe__ingredients'
        )
        if not shopping_cart_items.exists():
            return HttpResponse(
                {'detail': 'Ваша корзина покупок пуста'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ingredients = {}
        for item in shopping_cart_items:
            for ingredient in item.recipe.ingredients.all():
                key = (ingredient.name, ingredient.measurement_unit)
                if key in ingredients:
                    ingredients[key] += ingredient.name
                else:
                    ingredients[key] = ingredient.name
        text_lines = []
        for name, unit in ingredients.items():
            text_lines.append(f"{name} - {unit}\n")
        response = HttpResponse(
            text_lines,
            content_type='text/plain; charset=utf-8'
        )
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user if \
            self.request.user.is_authenticated else None

        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited == '1':
            if user:
                queryset = queryset.filter(favorites=user)
            else:
                return queryset.none()

        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        if is_in_shopping_cart == '1':
            if user:
                queryset = queryset.filter(shoppingcart__user=user)
            else:
                return queryset.none()

        if self.request.query_params.get('author'):
            queryset = queryset.filter(
                author__id=self.request.query_params.get('author')
            )

        if self.request.query_params.get('tags'):
            queryset = queryset.filter(
                tags__slug__in=self.request.query_params.getlist('tags')
            )

        queryset = queryset.distinct()

        if self.request.query_params.get('limit'):
            queryset = queryset[:int(self.request.query_params.get('limit'))]

        return queryset
