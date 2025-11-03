# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

# Option 1: Simple registration
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'photo', 'role')
    search_fields = ('user__username', 'user__email', 'role')

# Option 2: Inline UserProfile in User admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profiles'
    fk_name = 'user'

# Extend default UserAdmin to include the profile inline
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

# Unregister default User and register new UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
