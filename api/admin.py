from xml.dom.minidom import Document

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from .forms import ConstructionObjectForm
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
    readonly_fields = ['photo', 'photo_preview']

    def photo_preview(self, obj):
        return mark_safe('<img src="{url}" width="100px" height="100px" />'.format(
            url=obj.photo.url,
        )
        )


class ReviewReportPhotoInline(admin.StackedInline):
    model = ReportPhoto
    extra = 0


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    inlines = [ReviewIssueInline, ReviewReportInline]

@admin.register(ConstructionObjectDocumentType)
class ConstructionObjectAdmin(admin.ModelAdmin):
    pass

class DocumentInline(admin.StackedInline):
    model = ConstructionObjectDocument
    extra = 0

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    pass

@admin.register(IssueType)
class IssueTypeAdmin(admin.ModelAdmin):
    pass

@admin.register(ConstructionCompany)
class ConstructionCompanyAdmin(admin.ModelAdmin):
    pass

@admin.register(ProjectDeveloperCompany)
class ProjectDeveloperCompanyAdmin(admin.ModelAdmin):
    pass

@admin.register(ConstructionObject)
class ConstructionObjectAdmin(admin.ModelAdmin):
    inlines = [DocumentInline]
    form = ConstructionObjectForm


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    inlines = [ReviewIssuePhotoInline]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    inlines = [ReviewReportPhotoInline]
