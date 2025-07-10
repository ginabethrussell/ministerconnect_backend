from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import User, Church, InviteCode


class CustomUserAdmin(UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    model = User
    list_display = ["email", "is_active", "is_staff"]  # Adjust as needed


# Register your models here.
admin.site.register(User, CustomUserAdmin)
admin.site.register(Church)
admin.site.register(InviteCode)
