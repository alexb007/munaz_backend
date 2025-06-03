from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView,
    ProfileView,
    ReviewListView,
    StartReviewView, ReportCreateView, ReportPhotoCreateView, IssueCreateView, IssuePhotoCreateView, IssueUpdateView,
)

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/me/', ProfileView.as_view(), name='profile'),
    path('reviews/', ReviewListView.as_view(), name='review-list'),
    path('reviews/<int:review_id>/start/', StartReviewView.as_view(), name='start-review'),

    path('reviews/<int:review_id>/reports/', ReportCreateView.as_view(), name='report-create'),
    path('reports/<int:report_id>/photos/', ReportPhotoCreateView.as_view(), name='report-photo-create'),

    path('reviews/<int:review_id>/issues/', IssueCreateView.as_view(), name='issue-create'),
    path('issues/<int:issue_id>/photos/', IssuePhotoCreateView.as_view(), name='issue-photo-create'),
    path('issues/<int:pk>/', IssueUpdateView.as_view(), name='issue-update'),
]