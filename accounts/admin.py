from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

# Профили не показываем отдельно — они создаются автоматом
# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     ...

# Расширяем встроенный список пользователей
class ProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'get_department', 'is_active')
    list_filter = ('profile__role', 'is_active')

    @admin.display(description='Роль')
    def get_role(self, obj):
        return obj.profile.get_role_display() if hasattr(obj, 'profile') else '—'

    @admin.display(description='Отдел')
    def get_department(self, obj):
        return obj.profile.department if hasattr(obj, 'profile') else '—'

# Перерегистрируем User
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)