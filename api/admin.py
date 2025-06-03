from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import *


# Register your models here.

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['email', 'username', 'phone', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone',)}),
    )


admin.site.register(User, CustomUserAdmin)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    pass

@admin.register(ConstructionObject)
class ConstructionObjectAdmin(admin.ModelAdmin):
    pass

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    pass
