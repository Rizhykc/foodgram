from django.core.exceptions import ValidationError

from recipes.models import Recipe, ShoppingCart
from users.models import Subscription


def validate_subscription(serializer, data):
    user = data['user']
    author = data['author']
    if user == author:
        raise ValidationError('Нельзя подписаться на самого себя')
    existing_subscription = Subscription.objects.filter(
        user=user, author=author).exists()
    if existing_subscription:
        raise ValidationError('Вы уже подписались на этого автора')
    return data


def validate_recipe(serializer, data):
    cooking_time = data.get('cooking_time')
    ingredients = data.get('ingredients')
    name = data.get('name')
    author = serializer.context['request'].user
    if cooking_time < 1:
        raise ValidationError(
            'Время приготовления должно быть не меньше одной минуты'
        )
    if ingredients:
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        unique_ingredient_ids = set(ingredient_ids)
        if len(ingredient_ids) != len(unique_ingredient_ids):
            raise ValidationError('Ингредиенты должны быть уникальны')
    if not getattr(
        serializer.instance, 'pk', None) and Recipe.objects.filter(
            name=name, author=author).exists():
        raise ValidationError('Вы уже добавили этот рецепт')
    return data


def validate_shopping_cart(serializer, data):
    user = data['user']
    recipe = data['recipe']
    if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
        raise ValidationError('Рецепт уже добавлен в корзину')
    return data
