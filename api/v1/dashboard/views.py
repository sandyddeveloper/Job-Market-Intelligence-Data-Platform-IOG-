from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg
from apps.jobs.models import JobPosting, Industry, Skill
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

class DashboardOverviewView(APIView):
    """
    Get aggregated KPIs and analytics metadata for the frontend dashboard.
    """
    @extend_schema(
        summary="Dashboard Overview Analytics",
        description="Fetch KPIs (total counts, average salaries, remote allowed ratios) and distributions for charts.",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Dashboard Analytics"]
    )
    def get(self, request, *args, **kwargs):
        # 1. KPIs
        total_jobs = JobPosting.objects.count()
        avg_salary = JobPosting.objects.filter(normalized_salary__gt=0).aggregate(Avg('normalized_salary'))['normalized_salary__avg']
        
        # 2. Remote Ratios
        remote_distribution = list(
            JobPosting.objects.values('remote_allowed')
            .annotate(count=Count('job_id'))
        )
        
        # 3. Work Type Allocation
        work_type_distribution = list(
            JobPosting.objects.values('work_type', 'formatted_work_type')
            .annotate(count=Count('job_id'))
            .order_by('-count')
        )
        
        # 4. Experience Level Distribution
        exp_level_distribution = list(
            JobPosting.objects.values('formatted_experience_level')
            .annotate(count=Count('job_id'))
            .order_by('-count')
        )
        
        # 5. Top Industries
        top_industries = list(
            Industry.objects.annotate(job_count=Count('job_postings'))
            .filter(job_count__gt=0)
            .order_by('-job_count')[:6]
            .values('industry_id', 'industry_name', 'job_count')
        )
        
        # 6. Top Skills
        top_skills = list(
            Skill.objects.annotate(job_count=Count('job_postings'))
            .filter(job_count__gt=0)
            .order_by('-job_count')[:10]
            .values('skill_abr', 'skill_name', 'job_count')
        )
        
        # 7. Data Source Distribution
        data_source_distribution = list(
            JobPosting.objects.values('data_source')
            .annotate(count=Count('job_id'))
        )
        
        return Response({
            "total_jobs": total_jobs,
            "average_salary_usd": float(avg_salary) if avg_salary else 0.0,
            "remote_distribution": remote_distribution,
            "work_type_distribution": work_type_distribution,
            "experience_level_distribution": exp_level_distribution,
            "top_industries": top_industries,
            "top_skills": top_skills,
            "data_source_distribution": data_source_distribution
        }, status=status.HTTP_200_OK)
