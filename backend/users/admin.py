from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import CustomUser, Subscription


@admin.register(CustomUser)
class UserAdmin(UserAdmin):

    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'date_joined',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('date_joined', 'email', 'first_name', 'is_staff')
    empty_value_display = '-пусто-'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user', 'author')


admin.site.empty_value_display = '-пусто-'
