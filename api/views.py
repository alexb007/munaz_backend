from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, generics, permissions, viewsets, filters
from .models import Review, Report, Issue, ReportPhoto, IssuePhoto, ConstructionObject, IssueType, \
    ConstructionObjectDocument
from .permissions import IsInspectorOrDeveloper
from .serializers import LoginSerializer, UserSerializer, ReviewSerializer, ReportSerializer, IssueSerializer, \
    ReportPhotoSerializer, IssuePhotoSerializer, ConstructionObjectSerializer, ConstructionDocumentSerializer, \
    IssueTypeSerializer, ConstructionObjectListSerializer, ReviewListSerializer
from django.contrib.auth import get_user_model
from django.db.models import Q, F
from geopy.distance import geodesic

User = get_user_model()


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class ConstructionsView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ConstructionObjectSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('name',)


    def get_serializer_class(self):
        if self.action == 'list':
            return ConstructionObjectListSerializer
        return ConstructionObjectSerializer

    def get_queryset(self):
        queryset = ConstructionObject.objects.all().select_related('owner', )
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
            'owner_companies', 'owner_companies__director', 'owner_companies__contact_person', 'owner_companies__personal',
            'project_companies', 'project_companies__director', 'project_companies__contact_person', 'project_companies__personal',
            'construction_companies', 'construction_companies__director', 'construction_companies__contact_person','construction_companies__personal')
        return queryset

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None, *args, **kwargs):
        queryset = self.get_object().documents.all()
        return Response(ConstructionDocumentSerializer(queryset, many=True, context={'request': request}).data)


class ConstructionDocumentsView(ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = ConstructionObjectDocument.objects.all()

    def get(self, request, *args, **kwargs):
        queryset = ConstructionObjectDocument.objects.all()
        serializer = ConstructionDocumentSerializer(queryset, many=True)
        return Response(serializer.data)


class InspectionsView(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    queryset = Review.objects.all().select_related('assigned_to', )
    permission_classes = [IsAuthenticated]
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('object', 'assigned_to')

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return ReviewListSerializer
        return ReviewSerializer

class IssuesView(viewsets.ModelViewSet):
    serializer_class = IssueSerializer
    queryset = Issue.objects.all().select_related('issue_type', 'created_by',).prefetch_related('photos')
    permission_classes = [IsAuthenticated]
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('review__object', 'issue_type')


class ReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('object',)

    def get_queryset(self):
        user = self.request.user
        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')

        queryset = Review.objects.filter(
            Q(assigned_to=user),
            status__in=['planned', 'in_progress']
        ).select_related('object', 'assigned_to').annotate(
            latitude=F('object__latitude'),
            longitude=F('object__longitude'),
        )
        #
        # if latitude and longitude:
        #     user_location = (float(latitude), float(longitude))
        #     reviews_in_radius = []
        #     for review in queryset:
        #         obj_location = (review.object.latitude, review.object.longitude)
        #         if geodesic(user_location, obj_location).meters <= 200:
        #             reviews_in_radius.append(review.id)
        #     queryset = queryset.filter(id__in=reviews_in_radius)

        return queryset


class StartReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):
        try:
            review = Review.objects.get(id=review_id, assigned_to=request.user)
            if review.status != 'planned':
                return Response(
                    {'error': 'Review cannot be started'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Проверка геолокации
            # latitude = request.data.get('latitude')
            # longitude = request.data.get('longitude')
            #
            # if latitude and longitude:
            #     user_location = (float(latitude), float(longitude))
            #     obj_location = (review.object.latitude, review.object.longitude)
            #     if geodesic(user_location, obj_location).meters > 200:
            #         return Response(
            #             {'error': 'You must be within 200 meters of the object'},
            #             status=status.HTTP_400_BAD_REQUEST
            #         )

            review.status = 'in_progress'
            review.save()
            return Response(ReviewSerializer(review).data)

        except Review.DoesNotExist:
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ReportCreateView(generics.CreateAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        review = get_object_or_404(Review, pk=self.kwargs['review_id'])
        serializer.save(review=review, created_by=self.request.user)


class IssueTypeView(generics.ListAPIView):
    queryset = IssueType.objects.all()
    serializer_class = IssueTypeSerializer


class ReportPhotoCreateView(generics.CreateAPIView):
    queryset = ReportPhoto.objects.all()
    serializer_class = ReportPhotoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        report = get_object_or_404(Report, pk=self.kwargs['report_id'])
        serializer.save(report=report)


class IssueCreateView(generics.CreateAPIView):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        review = get_object_or_404(Review, pk=self.kwargs['review_id'])
        serializer.save(review=review, created_by=self.request.user)


class IssuePhotoCreateView(generics.CreateAPIView):
    queryset = IssuePhoto.objects.all()
    serializer_class = IssuePhotoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        issue = get_object_or_404(Issue, pk=self.kwargs['issue_id'])
        serializer.save(issue=issue)


class IssueUpdateView(generics.UpdateAPIView):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    permission_classes = [permissions.IsAuthenticated, IsInspectorOrDeveloper]
    http_method_names = ['patch']
