[![Main foodgram workflow](https://github.com/Rizhykc/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/Rizhykc/foodgram/actions/workflows/main.yml)
# Проект: [foodgram](https://foodgram-blog.serveblog.net/)
### foodgram - сервис для публикации рецептов. Авторизованные пользователи могут подписываться на понравившихся авторов, добавлять рецепты в избранное, в покупки, скачать список покупок ингредиентов для добавленных в покупки рецептов.

### Что умеет проект:

**📝 Работа с рецептами:**
- Создание, редактирование и удаление собственных рецептов.
- Просмотр рецептов других пользователей.
**❤️ Избранное:**
- Добавление рецептов в избранное и их просмотр в отдельном разделе.
- Удаление рецептов из избранного.
**📌 Подписки на авторов:**
- Подписка на понравившихся кулинаров и отмена подписки.
- Просмотр рецептов избранных авторов в ленте.

## Содержание

- [Установка и настройка](#установка-и-настройка)
- [Автоматизация и развертывание](#автоматизация-и-развертывание)
- [Работа с проектом](#работа-с-проектом)

## Технологии
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Django](https://img.shields.io/badge/Django-3.2-0C4B33?style=flat-square&logo=django&logoColor=white&labelColor=0C4B33)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=github-actions&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?logo=nginx&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9.13-%23254F72?style=flat-square&logo=python&logoColor=yellow&labelColor=254f72)
![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)

## Установка и настройка

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/Rizhykc/foodgram.git
   cd foodgram
   ```

2. **Настройте переменные окружения:**
   - В корневой директории проекта создайте файл с именем .env (без расширения).
   - Скопируйте параметры подключения к PostgreSQL, как указано в примере из файла *.env.example.*
   - После заполнения файл должен остаться в корне проекта.
   # Важно: 
   - Замените your_db_name, your_db_user и your_db_password на свои реальные данные !
3. **Запустите Docker Compose:**
   ```bash
   docker-compose up --build
   ```

   Это запустит все контейнеры (backend, frontend, db, и gateway) и поднимет приложение.

## Автоматизация и развертывание

Проект настроен для автоматического тестирования и развертывания с помощью GitHub Actions:
- Проверка кода на соответствие PEP8.
- Запуск тестов для фронтенда и бэкенда.
- Сборка Docker образов и отправка их на Docker Hub.
- Обновление образов на сервере и перезапуск приложения.
- Сборка статики и выполнение миграций.
- Уведомления о завершении деплоя в Telegram.

## Работа с проектом

1. **Переход к интерфейсу приложения:**
   После запуска контейнеров, приложение доступно по [http://localhost](http://localhost:7000).

2. **После захода на сайт**
   Теперь вам осталось только зарегистрироваться и создать свой рецепт или добавить в избранное уже существующий

### Автор проекта: [*Рижук Сергей*](https://github.com/Rizhykc)