from rest_framework import serializers

from .models import ConstructionDailyProgress, ConstructionFinancing, PublicIssue, PublicIssuePhoto, User, \
    ConstructionObject, Review, ReportPhoto, Report, IssuePhoto, Issue, ConstructionCompany, \
    Person, IssueType, ConstructionObjectDocument, InspectionType, ProjectOwnerCompany, ProjectDeveloperCompany, \
    ConstructionObjectDocumentType, IssueAction, ReviewComment, IssueActionPhoto, ReviewCommentPhoto, Neighborhood, \
    GovermentProgram, Assignment


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    person = PersonSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone', 'avatar', 'person']


class IssueTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueType
        fields = '__all__'


class NeighborhoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Neighborhood
        fields = '__all__'


class ConstructionDocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConstructionObjectDocumentType
        fields = '__all__'


class ConstructionDocumentSerializer(serializers.ModelSerializer):
    file_size = serializers.SerializerMethodField()

    def get_file_size(self, obj):
        if obj.file:
            return obj.file.size
        return None

    def get_document_type(self, obj):
        return obj.document_type.title

    class Meta:
        model = ConstructionObjectDocument
        fields = '__all__'





class ProjectOwnerCompanySerializer(serializers.ModelSerializer):
    personal = PersonSerializer(many=True, read_only=True)
    director = PersonSerializer(read_only=True)
    contact_person = PersonSerializer(read_only=True)


    class Meta:
        model = ProjectOwnerCompany
        fields = '__all__'


class ProjectDeveloperCompanySerializer(serializers.ModelSerializer):
    personal = PersonSerializer(many=True, read_only=True)
    director = PersonSerializer(read_only=True)
    contact_person = PersonSerializer(read_only=True)

    class Meta:
        model = ProjectDeveloperCompany
        fields = '__all__'


class ConstructionCompanySerializer(serializers.ModelSerializer):
    personal = PersonSerializer(many=True, read_only=True)
    director = PersonSerializer(read_only=True)
    contact_person = PersonSerializer(read_only=True)

    class Meta:
        model = ConstructionCompany
        fields = '__all__'


class ConstructionObjectSerializer(serializers.ModelSerializer):
    owner_companies = ProjectOwnerCompanySerializer(many=True, read_only=True)
    project_companies = ProjectDeveloperCompanySerializer(many=True, read_only=True)
    construction_companies = ConstructionCompanySerializer(many=True, read_only=True)
    financed = serializers.FloatField(default=0)
    completed = serializers.FloatField(default=0)
    p_reviews = serializers.FloatField(default=0)

    class Meta:
        model = ConstructionObject
        fields = '__all__'#[f.name for f in ConstructionObject._meta.fields] + ['construction_companies', 'project_companies', 'owner_companies', 'financed']


class InspectionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionType
        fields = '__all__'

class ReportPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportPhoto
        fields = ['id', 'photo', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class ReportSerializer(serializers.ModelSerializer):
    photos = ReportPhotoSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at']

class ReviewListSerializer(serializers.ModelSerializer):
    assigned_to = UserSerializer(read_only=True)
    latitude = serializers.FloatField(read_only=True)
    longitude = serializers.FloatField(read_only=True)
    inspection_types = InspectionTypeSerializer( many=True)
    reports = ReportSerializer(many=True)

    class Meta:
        model = Review
        fields = '__all__'


class BaseReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'


class ReviewSerializer(BaseReviewSerializer):
    object = ConstructionObjectSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    latitude = serializers.FloatField(read_only=True)
    longitude = serializers.FloatField(read_only=True)







class IssuePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssuePhoto
        fields = ['id', 'photo', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class IssueSerializer(serializers.ModelSerializer):
    photos = IssuePhotoSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['issue_type'] = IssueTypeSerializer(instance.issue_type, read_only=True, ).data
        return context

    class Meta:
        model = Issue
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class IssueActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueAction
        fields = '__all__'


class IssueActionPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueActionPhoto
        fields = '__all__'


class ReviewCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewComment
        fields = '__all__'


class ReviewCommentPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewCommentPhoto
        fields = '__all__'


class GovernmentProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = GovermentProgram
        fields = '__all__'

class CreatePublicIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicIssue
        fields = '__all__'


class PublicIssuePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicIssuePhoto
        fields = '__all__'


class PublicIssueSerializer(serializers.ModelSerializer):
    photos = PublicIssuePhotoSerializer(read_only=True, many=True)
    class Meta:
        model = PublicIssue
        fields = '__all__'


class CreateConstructionFinancingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConstructionFinancing
        fields = '__all__'

class ConstructionFinancingSerializer(serializers.ModelSerializer):
    construction = ConstructionObjectSerializer(read_only=True)
    person = PersonSerializer(read_only=True)

    class Meta:
        model = ConstructionFinancing
        fields = '__all__'

class ConstructionDailyProgressSerializer(serializers.ModelSerializer):
    realtime = True
    construction = ConstructionObjectSerializer(read_only=True)

    class Meta:
        model = ConstructionDailyProgress
        fields = '__all__'


class AggregationSerializer(serializers.Serializer):
    function = serializers.ChoiceField(
        choices=["count", "sum", "avg", "min", "max"],
        required=False,
    )
    field = serializers.CharField(required=False)
    group_by = serializers.CharField(required=False)
    

class ReportBlockSerializer(serializers.Serializer):
    id = serializers.CharField()
    type = serializers.ChoiceField(
        choices=["row", "kpi", "table", "lineChart", "barChart", "pieChart"]
    )
    children = serializers.ListField(
        child=serializers.DictField(), # Or another CategorySerializer instance
        required=False
    )
    entity = serializers.CharField(required=False)
    fields = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    aggregation = AggregationSerializer(required=False)
    pagination = serializers.DictField(required=False)

    def get_children(self, obj):
        return ReportBlockSerializer(obj.children, many=True).data

    class Meta:
        fields = ["id", "type", "children", "entity", "fields", "aggregation", "pagination"]

class ReportQuerySerializer(serializers.Serializer):
    report_id = serializers.CharField()
    filters = serializers.DictField(required=False)
    annotations = serializers.DictField(required=False)
    period = serializers.DictField(required=False)
    period_by = serializers.CharField(default='created_at',required=False)
    blocks = ReportBlockSerializer(many=True)


class ConstructionObjectListSerializer(serializers.ModelSerializer):
    owner_companies = ProjectOwnerCompanySerializer(many=True, read_only=True)
    project_companies = ProjectDeveloperCompanySerializer(many=True, read_only=True)
    construction_companies = ConstructionCompanySerializer(many=True, read_only=True)
    financed = serializers.FloatField(default=0)
    financed_p = serializers.FloatField(default=0)
    completed = serializers.FloatField(default=0)
    completed_p = serializers.FloatField(default=0)
    p_reviews = serializers.FloatField(default=0)
    i_reviews = serializers.FloatField(default=0)
    t_reviews = serializers.FloatField(default=0)
    neighborhood = NeighborhoodSerializer(read_only=True)
    program = GovernmentProgramSerializer(read_only=True)

    class Meta:
        model = ConstructionObject
        fields = '__all__'

class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = '__all__'