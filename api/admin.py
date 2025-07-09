from django.contrib import admin
from .models import User, Church, InviteCode

# Register your models here.
admin.site.register(User)
admin.site.register(Church)
admin.site.register(InviteCode)
