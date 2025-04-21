from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.db import models

from foodgram.constants import MAX_TEXT_LENGTH, TEXT_LENGTH

from .manager import CustomUserManager


class CustomUser(AbstractUser):
    """Кастомная модель пользователя с дополнительными полями."""
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=TEXT_LENGTH,
        validators=[
            RegexValidator(
                regex=r'^[А-Яа-яЁёA-Za-z]+$',
                message='Поле должно содержать только буквы',
                code='invalid_name',
            ),
        ],
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=TEXT_LENGTH,
        validators=[
            RegexValidator(
                regex=r'^[А-Яа-яЁёA-Za-z]+$',
                message='Поле должно содержать только буквы',
                code='invalid_name',
            ),
        ],
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
    avatar = models.ImageField('Аватар', upload_to='users/',
                               blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name', )

    objects = CustomUserManager()

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
        related_name='subscribing'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='subscriber'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
