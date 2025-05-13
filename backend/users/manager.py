from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError


class UserAccountManager(BaseUserManager):
    """
        Кастомный менеджер реализует методы добавления:
        пользователей, администраторов.
    """
    def _initialize_user(
            self, email, username, first_name, last_name, password
    ):
        """Инициализация нового пользовательского аккаунта"""
        return self.model(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password
        )

    def _validate_credentials(self, email):
        """Проверка обязательных учетных данных"""
        if not email:
            raise ValidationError('Требуется указать email')
        return self.normalize_email(email)

    def create_user(
            self, email, username, first_name, last_name, password
    ):
        """
            Регистрация нового пользователя в системе
            с указанными учетными данными
        """
        processed_email = self._validate_credentials(email)
        new_user = self._initialize_user(
            email=processed_email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        if password:
            new_user.set_password(password)
        new_user.save(using=self._db)

        return new_user

    def create_superuser(
            self, email, username, first_name, last_name, password
    ):
        """
        Создание учетной записи с административными привилегиями
        """
        admin = self.create_user(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        admin.is_active = True
        admin.is_admin = True
        admin.is_staff = True
        admin.is_superuser = True
        admin.save(using=self._db)

        return admin
