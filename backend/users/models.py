from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from api.validators import validate_name
from foodgram.constants import MAX_TEXT_LENGTH, TEXT_LENGTH
from users.manager import UserAccountManager


class CustomUser(AbstractUser):
    """Кастомная модель пользователя."""
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=TEXT_LENGTH,
        validators=[validate_name],
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=TEXT_LENGTH,
        validators=[validate_name],
    )
    username = models.CharField(
        verbose_name='Никнейм',
        max_length=TEXT_LENGTH,
        unique=True,
        error_messages={
            'unique': 'Никнейм занят.',
        },
        validators=[UnicodeUsernameValidator()]
    )
    email = models.EmailField(
        verbose_name='Email',
        max_length=MAX_TEXT_LENGTH,
        unique=True
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='users/',
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name', )

    objects = UserAccountManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username', )

    def __str__(self):
        return self.username

    @property
    def subscriptions(self):
        return CustomUser.objects.filter(
            subscribers__user=self
        )

    @property
    def subscribers(self):
        return CustomUser.objects.filter(
            subscriptions__author=self
        )


class Subscription(models.Model):
    """Модель подписки пользователей друг на друга."""
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='subscriptions'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='subscribers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
