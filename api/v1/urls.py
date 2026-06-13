from django.urls import path
from api.v1.user.views import UserLoginView, JobPostListView, ResumeUploadView

urlpatterns = [
    path('auth/login/', UserLoginView.as_view(), name='api-auth-login'),
    path('jobs/', JobPostListView.as_view(), name='api-job-list'),
    path('resume/parse/', ResumeUploadView.as_view(), name='api-resume-parse'),
]
