from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from apps.jobs.models import JobPosting
from api.v1.jobs.serializers import JobPostingSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

class JobPostListView(APIView):
    """
    Search and browse Job Postings indexed on the platform.
    """
    @extend_schema(
        summary="List Job Postings",
        description="Query the index of jobs with search terms, location, remote status, work type, experience level, and salary filters.",
        parameters=[
            OpenApiParameter(name="q", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Search terms for job title, company name, or description.", required=False),
            OpenApiParameter(name="location", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Filter listings by location.", required=False),
            OpenApiParameter(name="remote_allowed", type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, description="Filter for remote positions.", required=False),
            OpenApiParameter(name="work_type", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Filter by work type (e.g. FULL_TIME, CONTRACT, PART_TIME, OTHER).", required=False),
            OpenApiParameter(name="experience_level", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Filter by experience level (e.g. 'Entry level', 'Associate', 'Mid-Senior level', 'Director', 'Executive').", required=False),
            OpenApiParameter(name="min_salary", type=OpenApiTypes.DECIMAL, location=OpenApiParameter.QUERY, description="Minimum annualized salary in USD.", required=False),
            OpenApiParameter(name="industry_id", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="Filter by industry ID.", required=False),
            OpenApiParameter(name="skill_abr", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Filter by skill abbreviation.", required=False),
            OpenApiParameter(name="limit", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="Number of results to return (default 10).", required=False),
            OpenApiParameter(name="offset", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="The starting index from which to return results.", required=False)
        ],
        responses={200: JobPostingSerializer(many=True), 400: OpenApiTypes.OBJECT},
        tags=["Job Postings"]
    )
    def get(self, request, *args, **kwargs):
        queryset = JobPosting.objects.select_related('company').prefetch_related('industries', 'skills').all().order_by('-listed_time', '-job_id')
        
        q = request.query_params.get("q")
        location = request.query_params.get("location")
        remote_allowed = request.query_params.get("remote_allowed")
        work_type = request.query_params.get("work_type")
        experience_level = request.query_params.get("experience_level")
        min_salary = request.query_params.get("min_salary")
        industry_id = request.query_params.get("industry_id")
        skill_abr = request.query_params.get("skill_abr")
        
        # Apply filters
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | 
                Q(company_name__icontains=q) | 
                Q(description__icontains=q)
            )
        if location:
            queryset = queryset.filter(location__icontains=location)
        if remote_allowed is not None:
            val = remote_allowed.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(remote_allowed=val)
        if work_type:
            queryset = queryset.filter(work_type=work_type)
        if experience_level:
            queryset = queryset.filter(formatted_experience_level=experience_level)
        if min_salary:
            try:
                min_sal_val = float(min_salary)
                queryset = queryset.filter(normalized_salary__gte=min_sal_val)
            except ValueError:
                return Response({"error": "Invalid min_salary query parameter value."}, status=status.HTTP_400_BAD_REQUEST)
        if industry_id:
            try:
                ind_id_val = int(industry_id)
                queryset = queryset.filter(industries__industry_id=ind_id_val)
            except ValueError:
                return Response({"error": "Invalid industry_id query parameter value."}, status=status.HTTP_400_BAD_REQUEST)
        if skill_abr:
            queryset = queryset.filter(skills__skill_abr=skill_abr)
            
        # Pagination
        try:
            limit = min(int(request.query_params.get("limit", 10)), 100)
            offset = max(int(request.query_params.get("offset", 0)), 0)
        except ValueError:
            return Response({"error": "Invalid limit or offset parameters."}, status=status.HTTP_400_BAD_REQUEST)
            
        total_count = queryset.count()
        sliced_queryset = queryset[offset:offset+limit]
        
        serializer = JobPostingSerializer(sliced_queryset, many=True)
        return Response({
            "count": total_count,
            "limit": limit,
            "offset": offset,
            "results": serializer.data
        }, status=status.HTTP_200_OK)
