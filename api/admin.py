from xml.dom.minidom import Document

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User as BaseUser
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin, StackedInline

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin

from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .forms import ConstructionObjectForm
from .models import *


# Register your models here.

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['email', 'username', 'phone', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone',)}),
    )



admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms`
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


class ReviewReportInline(StackedInline):
    model = Report
    extra = 0
    tab = True


class ReviewIssueInline(StackedInline):
    model = Issue
    extra = 0
    tab = True



class ReviewIssuePhotoInline(StackedInline):
    model = IssuePhoto
    extra = 0
    tab = True
    readonly_fields = ['photo', 'photo_preview']

    def photo_preview(self, obj):
        return mark_safe('<img src="{url}" width="100px" height="100px" />'.format(
            url=obj.photo.url,
        )
    )


class ReviewReportPhotoInline(StackedInline):
    model = ReportPhoto
    extra = 0


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    inlines = [ReviewIssueInline, ReviewReportInline]

@admin.register(ConstructionObjectDocumentType)
class ConstructionObjectAdmin(ModelAdmin):
    pass

class DocumentInline(StackedInline):
    model = ConstructionObjectDocument
    extra = 0

@admin.register(Person)
class PersonAdmin(ModelAdmin):
    pass

@admin.register(IssueType)
class IssueTypeAdmin(ModelAdmin):
    pass

@admin.register(ConstructionCompany)
class ConstructionCompanyAdmin(ModelAdmin):
    pass

@admin.register(ProjectDeveloperCompany)
class ProjectDeveloperCompanyAdmin(ModelAdmin):
    pass

@admin.register(ConstructionObject)
class ConstructionObjectAdmin(ModelAdmin):
    inlines = [DocumentInline]
    form = ConstructionObjectForm


@admin.register(Issue)
class IssueAdmin(ModelAdmin):
    inlines = [ReviewIssuePhotoInline]


@admin.register(Report)
class ReportAdmin(ModelAdmin):
    inlines = [ReviewReportPhotoInline]
