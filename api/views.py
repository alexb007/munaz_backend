from django.contrib.auth import get_user_model
from django.db.models import Q, F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, generics, permissions, viewsets, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.generics import get_object_or_404, ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import BruteforceProtectedJWTAuthentication
from .models import Review, Report, Issue, ReportPhoto, IssuePhoto, ConstructionObject, IssueType, \
    ConstructionObjectDocument, InspectionType, ProjectDeveloperCompany, Person, ProjectOwnerCompany, \
    ConstructionCompany, LoginAttempt, ConstructionObjectDocumentType
from .permissions import IsInspectorOrDeveloper
from .serializers import UserSerializer, ReviewSerializer, ReportSerializer, IssueSerializer, \
    ReportPhotoSerializer, IssuePhotoSerializer, ConstructionObjectSerializer, ConstructionDocumentSerializer, \
    IssueTypeSerializer, ConstructionObjectListSerializer, ReviewListSerializer, BaseReviewSerializer, \
    InspectionTypeSerializer, PersonSerializer, ProjectDeveloperCompanySerializer, ProjectOwnerCompanySerializer, \
    ConstructionCompanySerializer, ConstructionDocumentTypeSerializer
from .utils import unblock_user, get_user_login_stats

User = get_user_model()


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
                'owner_companies', 'owner_companies__director', 'owner_companies__contact_person',
                'owner_companies__personal',
                'project_companies', 'project_companies__director', 'project_companies__contact_person',
                'project_companies__personal',
                'construction_companies', 'construction_companies__director', 'construction_companies__contact_person',
                'construction_companies__personal')
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


class ConstructionDocumentTypeView(viewsets.ModelViewSet):
    serializer_class = ConstructionDocumentTypeSerializer
    queryset = ConstructionObjectDocumentType.objects.all()


class ConstructionObjectDocumentsView(viewsets.ModelViewSet):
    serializer_class = ConstructionDocumentSerializer
    queryset = ConstructionObjectDocument.objects.all()
    permission_classes = [IsAuthenticated, ]
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('construction', 'document_type',)


class InspectionTypesView(ListAPIView):
    serializer_class = InspectionTypeSerializer
    queryset = InspectionType.objects.all()


class InspectionsView(viewsets.ModelViewSet):
    serializer_class = BaseReviewSerializer
    queryset = Review.objects.all().select_related('assigned_to', )
    permission_classes = [IsAuthenticated]
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('object', 'assigned_to')

    def get_queryset(self):
        return Review.objects.all().select_related('assigned_to', 'object', 'created_by').prefetch_related('reports', 'inspection_types')

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return ReviewListSerializer
        return BaseReviewSerializer

    @action(detail=False, methods=['get'])
    def inspectors(self, request, pk=None, *args, **kwargs):
        companies = ProjectDeveloperCompany.objects.filter(personal__in=[request.user.person])
        if companies is not None and companies.count() > 0:
            queryset = companies.first().personal.all()
            serializer = PersonSerializer(queryset, many=True)
            return Response(serializer.data)
        return Response([])


class PersonView(viewsets.ModelViewSet):
    serializer_class = PersonSerializer
    queryset = Person.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)


class IssuesView(viewsets.ModelViewSet):
    serializer_class = IssueSerializer
    queryset = Issue.objects.all().select_related('issue_type', 'created_by', ).prefetch_related('photos')
    permission_classes = [IsAuthenticated]
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('review', 'review__object', 'issue_type')


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


class ProjectCompanyView(viewsets.ModelViewSet):
    serializer_class = ProjectDeveloperCompanySerializer
    queryset = ProjectDeveloperCompany.objects.all()
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('name',)
    permission_classes = [IsAuthenticated, ]


class ProjectOwnerCompanyView(viewsets.ModelViewSet):
    serializer_class = ProjectOwnerCompanySerializer
    queryset = ProjectOwnerCompany.objects.all()
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('name',)
    permission_classes = [IsAuthenticated, ]


class ConstructionCompanyView(viewsets.ModelViewSet):
    serializer_class = ConstructionCompanySerializer
    queryset = ConstructionCompany.objects.all()
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('name',)
    permission_classes = [IsAuthenticated, ]


@api_view(['POST'])
@permission_classes([IsAdminUser])
def unblock_user_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        unblock_user(user)
        return Response({
            'message': f'User {user.username} has been unblocked'
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_login_stats(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        stats = get_user_login_stats(user)
        return Response(stats, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def custom_token_obtain_pair(request):
    """
    Кастомный endpoint для получения токена с защитой от брутфорса
    """
    from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

    authenticator = BruteforceProtectedJWTAuthentication()
    ip_address = authenticator.get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    serializer = TokenObtainPairSerializer(data=request.data)
    print('asd')

    if serializer.is_valid():
        # Успешная аутентификация
        user = serializer.user
        LoginAttempt.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            successful=True
        )
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    else:
        print("ASD")
        # Неудачная аутентификация
        username = request.data.get('username')
        if username:
            try:
                user = User.objects.get(username=username)
                authenticator.handle_failed_attempt(username, ip_address, user_agent, request)
            except User.DoesNotExist:
                authenticator.log_failed_attempt_for_nonexistent_user(username, ip_address, user_agent)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
