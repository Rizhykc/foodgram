from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    """
        Кастомный менеджер реализует методы добавления:
        пользователей, администраторов.
    """
    def create_user(
            self, email, username, first_name, last_name, password
    ):
        """"Создание и возвращение пользователя."""
        if not email:
            raise ValueError('Поле email не может быть пустым')
        email = self.normalize_email(email)
        user = self.model(
            email=email, username=username,
            first_name=first_name, last_name=last_name
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(
            self, email, username, first_name, last_name, password
    ):
        """создание и возвращения админа"""
        user = self.create_user(
            email, username, first_name, last_name, password
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user
