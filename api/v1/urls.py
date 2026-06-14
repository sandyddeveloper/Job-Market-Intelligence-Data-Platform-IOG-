from django.urls import path
from api.v1.user.views import UserLoginView, ResumeUploadView
from api.v1.jobs.views import JobPostListView
from api.v1.dashboard.views import DashboardOverviewView
from api.v1.benchmarks.views import (
    DataScienceBenchmarkTrendsView, DataAnalystBenchmarkStatsView,
    APISalaryHistoryView, APISalaryHistogramView, APITopCompanyStandingsView
)

urlpatterns = [
    # Auth & Resume
    path('auth/login/', UserLoginView.as_view(), name='api-auth-login'),
    path('resume/parse/', ResumeUploadView.as_view(), name='api-resume-parse'),
    
    # Dashboard Analytics
    path('dashboard/overview/', DashboardOverviewView.as_view(), name='api-dashboard-overview'),
    
    # Jobs list and search (Database-backed)
    path('jobs/', JobPostListView.as_view(), name='api-job-list'),
    
    # Salary Benchmarks
    path('benchmarks/ds-trends/', DataScienceBenchmarkTrendsView.as_view(), name='api-benchmarks-ds-trends'),
    path('benchmarks/da-stats/', DataAnalystBenchmarkStatsView.as_view(), name='api-benchmarks-da-stats'),
    path('benchmarks/history/', APISalaryHistoryView.as_view(), name='api-benchmarks-history'),
    path('benchmarks/histogram/', APISalaryHistogramView.as_view(), name='api-benchmarks-histogram'),
    path('benchmarks/top-companies/', APITopCompanyStandingsView.as_view(), name='api-benchmarks-top-companies'),
]
