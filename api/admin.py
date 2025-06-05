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

class ReviewReportInline(admin.StackedInline):
    model = Report
    extra = 0

class ReviewIssueInline(admin.StackedInline):
    model = Issue
    extra = 0

class ReviewIssuePhotoInline(admin.StackedInline):
    model = IssuePhoto
    extra = 0

class ReviewReportPhotoInline(admin.StackedInline):
    model = ReportPhoto
    extra = 0


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    inlines = [ReviewIssueInline, ReviewReportInline]


@admin.register(ConstructionObject)
class ConstructionObjectAdmin(admin.ModelAdmin):
    pass

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    inlines = [ReviewIssuePhotoInline]

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    inlines = [ReviewReportPhotoInline]
