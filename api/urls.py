from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ProfileView,
    ReviewListView,
    StartReviewView, ReportCreateView, ReportPhotoCreateView, IssueCreateView, IssuePhotoCreateView, IssueUpdateView,
    ConstructionsView, IssueTypeView, InspectionsView, IssuesView, InspectionTypesView, ProjectCompanyView,
    ProjectOwnerCompanyView, ConstructionCompanyView, PersonView, ConstructionObjectDocumentsView,
    ConstructionDocumentTypeView, IssueActionViewSet, ReviewCommentViewSet
)

router = DefaultRouter()
router.register('objects', ConstructionsView, 'projects')
router.register('documents', ConstructionObjectDocumentsView, 'documents')
router.register('document-types', ConstructionDocumentTypeView, 'document-types')
router.register('inspections', InspectionsView, 'inspections')
router.register('issues', IssuesView, 'issues')
router.register('persons', PersonView, 'persons')
router.register('project-companies', ProjectCompanyView, 'project-companies')
router.register('owner-companies', ProjectOwnerCompanyView, 'owner-companies')
router.register('construction-companies', ConstructionCompanyView, 'construction-companies')
router.register('issue-actions', IssueActionViewSet, 'issue-actions')
router.register('review-comments', ReviewCommentViewSet, 'review-comments')

urlpatterns = [
    path('users/me/', ProfileView.as_view(), name='profile'),
    path('reviews/', ReviewListView.as_view(), name='review-list'),
    path('reviews/<int:review_id>/start/', StartReviewView.as_view(), name='start-review'),

    path('reviews/<int:review_id>/reports/', ReportCreateView.as_view(), name='report-create'),
    path('reports/<int:report_id>/photos/', ReportPhotoCreateView.as_view(), name='report-photo-create'),

    path('reviews/<int:review_id>/issues/', IssueCreateView.as_view(), name='issue-create'),
    path('issue_types/', IssueTypeView.as_view(), name='issue-type-list'),
    path('inspection_types/', InspectionTypesView.as_view(), name='inspection-type-list'),
    path('issues/<int:issue_id>/photos/', IssuePhotoCreateView.as_view(), name='issue-photo-create'),
    path('issues/<int:pk>/', IssueUpdateView.as_view(), name='issue-update'),
]

urlpatterns += router.urls
