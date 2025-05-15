from django.db.models import Count, Exists, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.pagination import CustomPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (AvatarSerializer, CustomUserCreateSerializer,
                             CustomUserSerializer, FavoriteSerializer,
                             IngredientSerializer, RecipeIngredient,
                             RecipeReadSerializer, RecipeWriteSerializer,
                             SubscriptionGetSerializer, SubscriptionSerializer,
                             TagSerializer)
from api.filters import IngredientFilter, RecipeFilter
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import CustomUser, Subscription


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Вьюсет для работы с пользователями."""
    queryset = CustomUser.objects.annotate(recipes_count=Count('recipes'))
    serializer_class = CustomUserCreateSerializer
    pagination_class = CustomPagination
    permission_classes = (permissions.AllowAny,)

    def get_serializer_class(self):
        """Возвращает нужный сериализатор в зависимости от действия."""
        if self.action in ['create']:
            return CustomUserCreateSerializer
        if self.action in ['list', 'retrieve', 'me']:
            return CustomUserSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in ['me', 'avatar', 'delete_avatar',
                           'subscriptions', 'subscribe']:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    @action(
        ['GET'],
        detail=False,
        url_path='me',
        url_name='me'
    )
    def me(self, request):
        """Получить информацию o текущем пользователе."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['PUT'],
        detail=False,
        url_path='me/avatar',
        url_name='avatar'
    )
    def avatar(self, request, *args, **kwargs):
        """Обновить аватар пользователя."""
        serializer = AvatarSerializer(
            instance=request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        """Удалить аватар пользователя."""
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['GET'],
        detail=False,
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def subscriptions(self, request):
        """Получить список подписок пользователя."""
        subscriptions = Subscription.objects.filter(subscriber=request.user)
        authors = [subscription.author for subscription in subscriptions]
        page = self.paginate_queryset(authors)
        serializer = SubscriptionGetSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        url_path='subscribe',
    )
    def subscribe(self, request, pk=None):
        """Подписаться или отписаться от автора."""
        user = request.user
        author = get_object_or_404(CustomUser, pk=pk)
        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={'subscriber': user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            subscription = serializer.save()
            return Response(
                SubscriptionSerializer(
                    subscription,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            deleted_count, _ = Subscription.objects.filter(
                subscriber=user,
                author=author
            ).delete()
            if not deleted_count:
                return Response(
                    {'errors': 'Вы не подписаны на этого автора.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы c тегами."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы c ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы c рецептами."""
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        """"Возвращает queryset рецептов для зарагестрированных юзеров."""
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tag', 'recipe_ingredients__ingredient'
        )
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(recipe=OuterRef('pk'), user=user)
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(recipe=OuterRef('pk'),
                                                user=user)
                ),
            )
        return queryset

    def get_serializer_class(self):
        """Различные сериализаторы для операций чтения и записи."""
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        """Сохраняет рецепт с указанием автора."""
        serializer.save(author=self.request.user)

    def add_favorite_cart(self, request, model, pk, serializer):
        """Добавление рецепта из избранных."""
        message = '{} уже в избранном.'
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if model.objects.filter(recipe=recipe, user=user).exists():
            return Response(
                {'detail': message.format(recipe.name)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializers = serializer(
            data={'recipe': recipe.id, 'user': user.id},
            context={'request': request}
        )
        serializers.is_valid(raise_exception=True)
        serializers.save()
        return Response(
            serializers.data, status=status.HTTP_201_CREATED
        )

    def delete_favorite_cart(self, request, model, pk):
        """Удаление рецепта из избранных."""
        user = request.use
        deleted_count, _ = model.objects.filter(
            recipe__id=pk, user=user
        ).delete()
        if deleted_count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Рецепт не существует'},
                        status=status.HTTP_400_BAD_REQUEST,)

    def _handle_recipe_list_action(self, request, pk, model, serializer):
        if request.method == 'POST':
            return self.add_favorite_cart(self, request, model, pk, serializer)
        return self.delete_favorite_cart(self, request, model, pk, serializer)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавить или удалить рецепт из избранного."""
        return self._handle_recipe_list_action(
            request, pk, Favorite, FavoriteSerializer
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок в виде текстового файла."""
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total=Sum('amount'))

        shopping_list = "\n".join([
            f"{item['ingredient__name']} - {item['total']} "
            f"{item['ingredient__measurement_unit']}"
            for item in ingredients
        ])

        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = ('attachment; ',
                                           'filename="shopping_list.txt"')
        return response

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[permissions.AllowAny]
    )
    def short_link(self, request, pk=None):
        """Короткая ссылка на рецепт."""
        recipe = get_object_or_404(Recipe, pk=pk)
        return Response(
            {'short_link': request.build_absolute_uri(
                recipe.get_absolute_url()
            )},
            status=status.HTTP_200_OK
        )
