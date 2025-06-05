from django.core.validators import slug_re
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, ConstructionObject, Review, ReportPhoto, Report, IssuePhoto, Issue


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone', 'avatar']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        refresh = RefreshToken.for_user(user)
        return {
            'user': UserSerializer(user).data,
            'token': str(refresh.access_token),
            'refresh': str(refresh),
        }


class ConstructionObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConstructionObject
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    object = ConstructionObjectSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    latitude = serializers.FloatField(read_only=True)
    longitude = serializers.FloatField(read_only=True)

    class Meta:
        model = Review
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


class IssuePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssuePhoto
        fields = ['id', 'photo', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class IssueSerializer(serializers.ModelSerializer):
    photos = IssuePhotoSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Issue
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']
