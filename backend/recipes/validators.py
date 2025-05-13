from django.core.exceptions import ValidationError

from foodgram.constants import MIN_UNIT
from recipes.models import Favorite, Recipe, ShoppingCart
from users.models import Subscription


def validate_subscription(serializer, data):
    """"""
    user = data['user']
    author = data['author']
    if user == author:
        raise ValidationError('Нельзя подписаться на самого себя')
    if Subscription.objects.filter(user=user, author=author).exists():
        raise ValidationError('Вы уже подписались на этого автора')
    return data


def validate_ingredients(serializer, data):
    ingredients = data.get('ingredients', [])
    if not ingredients:
        raise ValidationError(
            'Рецепт должен содержать хотя бы один ингредиент.'
        )
    ingredient_ids = [item['ingredient'].id for item in ingredients]
    if len(ingredient_ids) != len(set(ingredient_ids)):
        raise ValidationError('Ингредиенты должны быть уникальными.')
    tags = data.get('tags', [])
    if not tags:
        raise ValidationError('Рецепт должен содержать хотя бы один тег.')
    name = data.get('name')
    author = serializer.context['request'].user
    if not serializer.instance and (Recipe.objects
                                    .filter(name=name, author=author)
                                    .exists()):
        raise ValidationError('Вы уже добавили этот рецепт.')
    cooking_time = data.get('cooking_time')
    if cooking_time < MIN_UNIT:
        raise ValidationError(
            'Время приготовления должно быть не меньше одной минуты'
        )
    return data


def validate_shopping_cart(serializer, data):
    """"""
    user = data['user']
    recipe = data['recipe']
    if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
        raise ValidationError('Рецепт уже добавлен в корзину')
    return data


def validate_amount(serializer, data):
    """"""
    if not data:
        ValidationError('Количество не может быть пустым.')
    return data


def validate_favorite(serializer, data):
    """"""
    if Favorite.objects.filter(**data).exists():
        raise ValidationError(
            'Рецепт уже добавлен в избранное.'
        )
    return data
