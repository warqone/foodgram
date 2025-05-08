from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.conf import settings
from djoser.serializers import SetPasswordSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (
    viewsets, permissions, pagination, response, status, filters)
from rest_framework.decorators import action

from api import serializers
from api.permissions import IsAdminOnly, IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    TagSerializer, IngredientSerializer,
    RecipeSerializer, RecipeCreateUpdateSerializer, SubscriptionSerializer)
from recipes.models import Recipe, Tag, Ingredient

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    pagination_class = pagination.LimitOffsetPagination
    queryset = User.objects.all()
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^username', '^email')
    serializer_class = serializers.UserSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    @action(detail=False, methods=['get', 'patch'], url_path='me',
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return response.Response(
                serializer.data, status=status.HTTP_200_OK)
        serializer = self.get_serializer(
            user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
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
        if request.method == 'PUT':
            user = request.user
            serializer = AvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return response.Response(
                serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            user = request.user
            user.avatar.delete()
            user.save()
            return response.Response(
                status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,  # Для работы с конкретным пользователем (id в URL)
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='subscribe'
    )
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)

        if request.method == 'POST':
            # Проверка на подписку на самого себя
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
            return response.Response(
                status=status.HTTP_204_NO_CONTENT
            )

    @action(detail=False, methods=['get'], url_path='subscriptions',
            permission_classes=[permissions.IsAuthenticated],
            pagination_class=pagination.LimitOffsetPagination)
    def subscriptions(self, request):
        user = request.user
        queryset = user.subscriptions.all()
        serializer = self.get_serializer(queryset, many=True)
        return response.Response(
            serializer.data, status=status.HTTP_200_OK)


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
    filter_backends = [filters.SearchFilter]
    search_fields = ['^name']
    pagination_class = None
    http_method_names = ['get']


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

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.query_params.get('is_favorited'):
            queryset = queryset.filter(favorites__user=self.request.user)

        if self.request.query_params.get('is_in_shopping_cart'):
            queryset = queryset.filter(shopping_carts__user=self.request.user)

        return queryset.distinct()
