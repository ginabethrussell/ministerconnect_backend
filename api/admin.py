from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import User, Church, InviteCode


class CustomUserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    model = User
    # Show all the fields you want, including requires_password_change
    list_display = BaseUserAdmin.list_display + ("requires_password_change",)
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {"fields": ("requires_password_change",)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {"fields": ("requires_password_change",)}),
    )


# Register your models here.
admin.site.register(User, CustomUserAdmin)
admin.site.register(Church)
admin.site.register(InviteCode)
