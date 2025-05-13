from django_filters.rest_framework import (BooleanFilter, CharFilter,
                                           FilterSet,
                                           ModelMultipleChoiceFilter)

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(FilterSet):
    favorite_filter = BooleanFilter(method='get_favorite_recipes')
    shopping_cart_filter = BooleanFilter(method='get_shopping_cart_recipes')
    tag_filter = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tag_filter',
                  'favorite_filter', 'shopping_cart_filter')

    def _get_current_user(self):
        """Получает текущего пользователя из запроса."""
        request = self.request
        return (
            request.user if request and request.user.is_authenticated else None
        )

    def get_favorite_recipes(self, queryset, field_name, should_filter):
        """Фильтрует избранные рецепты текущего пользователя."""
        current_user = self._get_current_user()
        if should_filter and current_user:
            return queryset.filter(favorites__user=current_user)
        return queryset

    def get_shopping_cart_recipes(self, queryset, field_name, should_include):
        """"Фильтрует рецепты в корзине покупок текущего пользователя."""
        user = self._get_current_user()
        if should_include and user:
            return queryset.filter(shopping_carts__user=user)
        return queryset

    def filter_by_tags(self, queryset, field_name, tags):
        """Фильтрует рецепты по тегам, указанным в параметрах запроса."""
        tag_values = self.request.query_params.getlist('tags')
        if tag_values:
            return queryset.filter(tags__slug__in=tag_values).distinct()
        return queryset


class IngredientFilter(FilterSet):

    name = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
