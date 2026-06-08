from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget
from .models import LoginAttempt, User
class LoginAttemptsResource(resources.ModelResource):
    user_full_name = fields.Field(attribute='user', column_name='fullname')
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(User, field='username')
    )

    def dehydrate_user_full_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return ""

    class Meta:
        model = LoginAttempt
        fields = ('id', 'user', 'timestamp', 'user_full_name', 'user_agent')