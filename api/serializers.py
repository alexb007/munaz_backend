from rest_framework import serializers

from .models import User, ConstructionObject, Review, ReportPhoto, Report, IssuePhoto, Issue, ConstructionCompany, \
    Person, IssueType, ConstructionObjectDocument, InspectionType, ProjectOwnerCompany, ProjectDeveloperCompany, \
    ConstructionObjectDocumentType, IssueAction, ReviewComment, IssueActionPhoto, ReviewCommentPhoto


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone', 'avatar']


class IssueTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueType
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


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = '__all__'


class ProjectOwnerCompanySerializer(serializers.ModelSerializer):
    personal = PersonSerializer(many=True, read_only=True)

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['director'] = PersonSerializer(instance.director).data
        context['contact_person'] = PersonSerializer(instance.contact_person).data
        return context

    class Meta:
        model = ProjectOwnerCompany
        fields = '__all__'


class ProjectDeveloperCompanySerializer(serializers.ModelSerializer):
    personal = PersonSerializer(many=True, read_only=True)

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['director'] = PersonSerializer(instance.director).data
        context['contact_person'] = PersonSerializer(instance.contact_person).data
        return context

    class Meta:
        model = ProjectDeveloperCompany
        fields = '__all__'


class ConstructionCompanySerializer(serializers.ModelSerializer):
    personal = PersonSerializer(many=True, read_only=True)

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['director'] = PersonSerializer(instance.director).data
        context['contact_person'] = PersonSerializer(instance.contact_person).data
        return context

    class Meta:
        model = ConstructionCompany
        fields = '__all__'


class ConstructionObjectSerializer(serializers.ModelSerializer):
    owner_companies = ProjectOwnerCompanySerializer(many=True, read_only=True)
    project_companies = ProjectDeveloperCompanySerializer(many=True, read_only=True)
    construction_companies = ConstructionCompanySerializer(many=True, read_only=True)

    class Meta:
        model = ConstructionObject
        fields = '__all__'


class ConstructionObjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConstructionObject
        exclude = ['project_companies', 'construction_companies', 'owner_companies']


class InspectionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionType
        fields = '__all__'


class ReviewListSerializer(serializers.ModelSerializer):
    assigned_to = UserSerializer(read_only=True)
    latitude = serializers.FloatField(read_only=True)
    longitude = serializers.FloatField(read_only=True)

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['inspection_types'] = InspectionTypeSerializer(instance.inspection_types, many=True).data
        context['reports'] = ReportSerializer(instance.reports, many=True, context=self.context).data
        return context

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
