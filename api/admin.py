from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin, StackedInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .forms import ConstructionObjectForm
from .models import *


# Register your models here.

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['email', 'username', 'phone', 'is_staff', 'role']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone',)}),
    )


admin.site.unregister(Group)


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'timestamp', 'successful']
    list_filter = ['successful', 'timestamp']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['user', 'ip_address', 'user_agent', 'timestamp', 'successful']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms`
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets[0][1]['fields'] += ('role', )
        return fieldsets


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
    readonly_fields = ['photo_preview']

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


@admin.register(InspectionType)
class InspectionTypeAdmin(ModelAdmin):
    pass


@admin.register(ProjectOwnerCompany)
class ProjectOwnerCompanyAdmin(ModelAdmin):
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
