import csv
import io
import uuid

from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.http import StreamingHttpResponse, HttpResponse
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.crypto import get_random_string
from django.utils.safestring import mark_safe
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.formats import base_formats
from twisted.protocols.wire import Echo
from unfold.admin import ModelAdmin, StackedInline
from unfold.contrib.filters.admin import RelatedDropdownFilter, ChoicesDropdownFilter
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .forms import ConstructionObjectForm, GenerateUsersForm
from .models import *

class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'password')
        export_order = fields

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin, ImportExportModelAdmin):
    resource_classes = [UserResource]
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    change_list_template = 'admin/auth/user/change_list.html'
    list_display = ('username', 'first_name', 'last_name', 'role')
    list_display_links = ('username', 'first_name', 'last_name', 'role')

    def get_export_resource_kwargs(self, request, *args, **kwargs):
        kwargs['encoding'] = 'utf-8'
        print('ENCODING')
        return kwargs

    def get_urls(self):
        """Injects custom generation route into default user admin URLs."""
        urls = super().get_urls()
        custom_urls = [
            path(
                'generate-users/',
                self.admin_site.admin_view(self.generate_users_view),
                name='generate_users'
            ),
        ]
        return custom_urls + urls

    def generate_users_view(self, request):
        if request.method == 'POST':
            form = GenerateUsersForm(request.POST)
            if form.is_valid():
                num_users = form.cleaned_data['num_users']

                # 1. Create an in-memory text buffer for the CSV
                buffer = io.StringIO()
                writer = csv.writer(buffer)

                # Write CSV header row
                writer.writerow(['Username', 'Email', 'First Name', 'Last Name'])

                # 2. Build the users list in memory first (extremely fast)
                users_to_create = []
                csv_rows = []

                for _ in range(num_users):
                    unique_id = uuid.uuid4().hex[:8]
                    username = f"user_{unique_id}"
                    email = f"{username}@example.com"
                    first_name = f"First_{unique_id}"
                    last_name = f"Last_{unique_id}"

                    # Instantiate User objects without saving to database yet
                    user_obj = User(
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                    )
                    # Set standard unusable or dummy encrypted password
                    password = get_random_string(14)
                    user_obj.set_password(password)

                    users_to_create.append(user_obj)
                    csv_rows.append([username, email, first_name, last_name, password])

                # 3. Save ALL users to the database in a SINGLE database query
                User.objects.bulk_create(users_to_create)

                # 4. Write all rows to the CSV buffer
                writer.writerows(csv_rows)

                # 5. Return the file download response
                response = HttpResponse(buffer.getvalue(), content_type="text/csv")
                response['Content-Disposition'] = f'attachment; filename="generated_users_{num_users}.csv"'
                return response
        else:
            form = GenerateUsersForm()

        context = {
            **self.admin_site.each_context(request),
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, "admin/generate_users.html", context)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets[0][1]['fields'] = {*fieldsets[0][1]['fields'], 'role'}
        return fieldsets

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
class ConstructionObjectAdminDocumentType(ModelAdmin):
    pass


class DocumentInline(StackedInline):
    model = ConstructionObjectDocument
    extra = 0


@admin.register(Person)
class PersonAdmin(ModelAdmin):
    search_fields = ['fullname']


@admin.register(IssueType)
class IssueTypeAdmin(ModelAdmin):
    pass


@admin.register(InspectionType)
class InspectionTypeAdmin(ModelAdmin):
    pass


@admin.register(ProjectOwnerCompany)
class ProjectOwnerCompanyAdmin(ModelAdmin):
    search_fields = ["name"]

@admin.register(ConstructionCompany)
class ConstructionCompanyAdmin(ModelAdmin):
    search_fields = ["name"]

@admin.register(ProjectDeveloperCompany)
class ProjectDeveloperCompanyAdmin(ModelAdmin):
    search_fields = ["name"]

@admin.register(ConstructionObject)
class ConstructionObjectAdmin(ModelAdmin):
    search_fields = ['name']
    autocomplete_fields = ['attached_person']
    inlines = [DocumentInline]
    form = ConstructionObjectForm
    list_display = (
        'id', 'name', 'created_at', 'updated_at', 'address',
        'neighborhood', 'category', 'building_count',
        'p_reviews_p_m', 'i_reviews_p_m', 't_reviews_p_m'
    )
    list_editable = ('category', 'building_count')
    list_display_links = ('id', 'name',)
    list_filter = (
        ('program', RelatedDropdownFilter),
        ('neighborhood', RelatedDropdownFilter),
        ('category', ChoicesDropdownFilter),
        ('owner_companies', RelatedDropdownFilter),
        ('construction_companies', RelatedDropdownFilter),
        ('project_companies', RelatedDropdownFilter),
        ('attached_person', RelatedDropdownFilter),
    )
    list_filter_submit = True
    filter_vertical = ('owner_companies', 'construction_companies', 'project_companies',)
    ordering = ('id', 'name')


@admin.register(Issue)
class IssueAdmin(ModelAdmin):
    inlines = [ReviewIssuePhotoInline]


@admin.register(Report)
class ReportAdmin(ModelAdmin):
    inlines = [ReviewReportPhotoInline]


class IssueActionPhotoInline(StackedInline):
    model = IssueActionPhoto
    extra = 0


@admin.register(IssueAction)
class IssueActionAdmin(ModelAdmin):
    inlines = [IssueActionPhotoInline]


class ReviewCommentPhotoInline(StackedInline):
    model = ReviewCommentPhoto
    extra = 0


@admin.register(ReviewComment)
class ReviewCommentAdmin(ModelAdmin):
    inlines = [ReviewCommentPhotoInline]


@admin.register(GovermentProgram)
class GovernmentProgramAdmin(ModelAdmin):
    pass


@admin.register(Region)
class RegionAdmin(ModelAdmin):
    pass


@admin.register(District)
class DistrictAdmin(ModelAdmin):
    pass


@admin.register(Neighborhood)
class NeighborhoodAdmin(ModelAdmin):
    pass


class PublicIssuePhotosInline(StackedInline):
    model = PublicIssuePhoto
    extra = 0


@admin.register(PublicIssue)
class PublicIssueAdmin(ModelAdmin):
    inlines = [PublicIssuePhotosInline, ]
    list_display = ['id', 'title', 'description', ]


@admin.register(ConstructionFinancing)
class ConstructionFinancingAdmin(ModelAdmin):
    list_display = ['id', 'construction', 'date', 'amount', 'person']


@admin.register(ConstructionDailyProgress)
class ConsturctionDailyProgressAdmin(ModelAdmin):
    list_display = ['id', 'construction', 'date', 'amount', 'workers', 'machines']


class AssignmentAttachmentInline(StackedInline):
    model = AssignmentAttachment
    extra = 0

@admin.register(Assignment)
class AssignmentAdmin(ModelAdmin):
    list_display = ('id', 'title', 'description', 'created_by', 'assigned_to', 'deadline', 'status')
    list_display_links = ('id', 'title', 'description', 'created_by', 'assigned_to', 'deadline', 'status')
    inlines = [AssignmentAttachmentInline]